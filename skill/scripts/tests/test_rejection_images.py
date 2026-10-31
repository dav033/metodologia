"""Images the owner attaches to a rejection in «Probar» reach every agent that acts on it (D-258). Owner, 2026-10-31:
«let me attach images to the rejection comments so the agents can see them».

The form is multipart (a plain multiple file input); the bytes are checked, stored under the requirement's
`evidence/owner-rejected/<SP>-v<N>/` with a name of our own, listed in the decision, the P-item and the panel, and
named with their absolute paths in the Solucionador's brief. A rejection without images keeps its old trigger key."""
from __future__ import annotations

import argparse
import hashlib
import http.client
import io
import json
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_rejection_images as images
import bt_verification as v
from test_verification import COMMIT, Base

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + bytes(range(256)) + b"\r\n--x\r\n"   # CRLF and a dash run inside
JPG = b"\xff\xd8\xff\xe0" + b"jpeg-body" * 10
GIF = b"GIF89a" + b"\x01\x00\x01\x00" + b"gif"
WEBP = b"RIFF\x10\x00\x00\x00WEBPVP8 " + b"webp"


def multipart(fields: dict, files: list[tuple[str, str, bytes]], boundary: str = "----btBoundary7MA4YWxkTrZu0gW"):
    out = b""
    for name, value in fields.items():
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n").encode()
    for field, filename, data in files:
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\n"
                "Content-Type: image/png\r\n\r\n").encode() + data + b"\r\n"
    return f"multipart/form-data; boundary={boundary}", out + f"--{boundary}--\r\n".encode()


class Limits(unittest.TestCase):
    def setUp(self):
        self.flags = {}
        p = patch("bt_config.get", side_effect=lambda key, default=None: self.flags.get(key, default))
        p.start()
        self.addCleanup(p.stop)


class Parsing(Limits):
    def test_fields_and_files_come_back_byte_for_byte(self):
        ctype, body = multipart({"token": "t", "anchor": "SP-1", "comments": "No carga «Nuevo»"},
                                [("images", "a.png", PNG), ("images", "b.jpg", JPG)])
        fields, files = images.parse_form(ctype, body)
        self.assertEqual(fields, {"token": "t", "anchor": "SP-1", "comments": "No carga «Nuevo»"})
        self.assertEqual(files, [("a.png", PNG), ("b.jpg", JPG)])

    def test_an_empty_file_input_sends_no_file(self):
        ctype, body = multipart({"token": "t"}, [("images", "", b"")])
        self.assertEqual(images.parse_form(ctype, body), ({"token": "t"}, []))

    def test_a_body_without_a_boundary_gives_nothing(self):
        self.assertEqual(images.parse_form("multipart/form-data", b"token=t"), ({}, []))
        self.assertEqual(images.parse_form("multipart/form-data; boundary=zz", b"garbage"), ({}, []))


class Checking(Limits):
    def test_the_bytes_decide_the_type_not_the_name(self):
        self.assertEqual([images.sniff(d) for d in (PNG, JPG, GIF, WEBP, b"<svg/>", b"RIFF\x00\x00\x00\x00WAVE")],
                         ["png", "jpg", "gif", "webp", "", ""])
        accepted = images.accept([("x.txt", PNG), ("y.png", GIF)])
        self.assertEqual([a["ext"] for a in accepted], ["png", "gif"])
        with self.assertRaises(images.Refused) as caught:
            images.accept([("ok.png", PNG), ("foto.png", b"<html><script>x</script>")])
        self.assertIn("«foto.png» no es una imagen PNG, JPEG, WebP ni GIF", str(caught.exception))
        self.assertIn("no guardé nada", str(caught.exception))

    def test_too_many_too_large_and_too_much_are_refused(self):
        self.assertEqual(images.accept([]), [])
        with self.assertRaises(images.Refused) as caught:
            images.accept([(f"{i}.png", PNG) for i in range(9)])
        self.assertIn("Adjuntaste 9 imágenes; el máximo es 8", str(caught.exception))
        self.flags.update({"rejections.max_image_mb": 1, "rejections.max_total_mb": 2})
        big = PNG + b"\x00" * (1024 * 1024)
        with self.assertRaises(images.Refused) as caught:
            images.accept([("grande.png", big)])
        self.assertIn("«grande.png» pesa 1.0 MB; el máximo es 1 MB por imagen", str(caught.exception))
        part = PNG + b"\x00" * (800 * 1024)
        with self.assertRaises(images.Refused) as caught:
            images.accept([("a.png", part), ("b.png", part), ("c.png", part)])
        self.assertIn("el máximo es 2 MB por rechazo", str(caught.exception))
        self.assertEqual(images.max_body(), 2 * 1024 * 1024 + images.FORM_OVERHEAD)

    def test_storage_uses_our_own_name_and_keeps_the_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp) / "REQ-1-x"
            stored = images.store(rdir, "SP-1", 2, images.accept([("../../../etc/passwd.png", PNG), ("b", JPG)]))
            sha = hashlib.sha256(PNG).hexdigest()
            self.assertEqual(stored[0], {"path": f"evidence/owner-rejected/SP-1-v2/1-{sha[:12]}.png", "sha256": sha,
                                         "type": "image/png", "bytes": len(PNG)})
            self.assertTrue(stored[1]["path"].endswith(f"/2-{hashlib.sha256(JPG).hexdigest()[:12]}.jpg"))
            self.assertEqual((rdir / stored[0]["path"]).read_bytes(), PNG)
            self.assertEqual(sorted(p.name for p in (rdir / "evidence/owner-rejected/SP-1-v2").iterdir()),
                             sorted(s["path"].rsplit("/", 1)[1] for s in stored))
            with self.assertRaises(images.Refused):
                images.store(rdir, "../SP-1", 2, images.accept([("a", PNG)]))

    def test_only_stored_images_are_served_with_the_type_their_bytes_say(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            rdir = project / "requirements" / "REQ-1-x"
            rel = "requirements/REQ-1-x/" + images.store(rdir, "SP-1", 1, images.accept([("a", GIF)]))[0]["path"]
            path, ctype = images.served(project, rel)
            self.assertEqual((path.read_bytes(), ctype), (GIF, "image/gif"))
            fake = rdir / "evidence/owner-rejected/SP-1-v1/2-0123456789ab.png"
            fake.write_text("<html>")
            (project / "secret.png").write_bytes(PNG)
            for bad in (rel.replace(".gif", ".md"), "requirements/REQ-1-x/evidence/owner-rejected/SP-1-v1/../../../../secret.png",
                        "secret.png", "requirements/REQ-1-x/SPEC.md", fake.relative_to(project).as_posix(), ""):
                self.assertIsNone(images.served(project, bad), bad)


class Decisions(Base):
    def setUp(self):
        super().setUp()
        self.pdir = self.rdir.parents[1]
        (self.pdir / "PENDING.md").write_text("# proj — Pending\n\n## Open\n_None_\n\n## Blocked\n_None_\n\n"
                                              "## Recently closed\n_None_\n", encoding="utf-8")
        self.projection(**{"SP-1": (1, COMMIT)})

    def entry(self):
        return v._load(self.rdir)["subplans"].get("SP-1")

    def test_a_rejection_with_images_records_them_in_the_decision_and_the_p_item(self):
        msg = v.decide("proj", self.rdir, "SP-1", "rejected", "el botón no responde", attachments=[("a.png", PNG), ("b", WEBP)])
        self.assertIn("Tu nota y las 2 imágenes quedaron guardadas y abrí el pendiente P-001", msg)
        found = self.entry()["attachments"]
        self.assertEqual([a["type"] for a in found], ["image/png", "image/webp"])
        self.assertTrue(all((self.rdir / a["path"]).is_file() for a in found))
        pending = (self.pdir / "PENDING.md").read_text(encoding="utf-8")
        self.assertIn(f"[imagen 1](requirements/REQ-009-demo/{found[0]['path']})", pending)
        self.assertIn(f"[imagen 2](requirements/REQ-009-demo/{found[1]['path']})", pending)
        import bt_pending
        items = bt_pending.parse(pending)[0]
        item = next(i for its in items.values() for i in its if i["id"] == "P-001")
        self.assertEqual((item["urgency"], item["complexity"]), ("high", "M"))

    def test_a_refused_image_records_nothing(self):
        before = (self.pdir / "PENDING.md").read_text(encoding="utf-8")
        msg = v.decide("proj", self.rdir, "SP-1", "rejected", "falla", attachments=[("x.png", b"not an image")])
        self.assertIn("no es una imagen", msg)
        self.assertIsNone(self.entry())
        self.assertEqual((self.pdir / "PENDING.md").read_text(encoding="utf-8"), before)
        self.assertFalse((self.rdir / "evidence").exists())

    def test_without_images_the_entry_and_the_trigger_key_are_as_before(self):
        v.decide("proj", self.rdir, "SP-1", "rejected", "falla  el\nbotón")
        dec = self.entry()
        self.assertNotIn("attachments", dec)
        note = hashlib.sha256("falla el botón".encode()).hexdigest()[:12]
        self.assertEqual(v.rejection_key("SP-1", dec), f"owner_rejected:SP-1:v1:{COMMIT[:12]}:{note}")

    def test_images_join_the_key_so_new_images_are_a_new_rejection(self):
        v.decide("proj", self.rdir, "SP-1", "rejected", "falla")
        plain = v.rejection_key("SP-1", self.entry())
        v.decide("proj", self.rdir, "SP-1", "rejected", "falla", attachments=[("a", PNG), ("b", GIF)])
        first = v.rejection_key("SP-1", self.entry())
        v.decide("proj", self.rdir, "SP-1", "rejected", "falla", attachments=[("b", GIF), ("a", PNG)])
        self.assertEqual(v.rejection_key("SP-1", self.entry()), first)              # the same images, in any order
        v.decide("proj", self.rdir, "SP-1", "rejected", "falla", attachments=[("c", JPG)])
        other = v.rejection_key("SP-1", self.entry())
        self.assertEqual(len({plain, first, other}), 3)
        self.assertTrue(other.startswith(f"owner_rejected:SP-1:v1:{COMMIT[:12]}:"))

    def test_an_approval_ignores_attachments(self):
        v.decide("proj", self.rdir, "SP-1", "approved", attachments=[("a", PNG)])
        self.assertNotIn("attachments", self.entry())
        self.assertFalse((self.rdir / "evidence").exists())

    def test_the_cli_attaches_files(self):
        import bt_cli_verify
        shot = Path(self.tmp.name) / "shot.png"
        shot.write_bytes(PNG)
        ns = argparse.Namespace(action="reject", req="REQ-009", subplan="SP-1", note="se ve mal", by="owner",
                                image=[str(shot)])
        with redirect_stdout(io.StringIO()) as out:
            bt_cli_verify.dispatch(ns, Path(self.tmp.name), "proj")
        self.assertIn("Tu nota y la imagen quedaron guardadas", out.getvalue())
        self.assertEqual(self.entry()["attachments"][0]["sha256"], hashlib.sha256(PNG).hexdigest())
        self.assertEqual(self.entry()["via"], "conversation")
        ns.image = [str(Path(self.tmp.name) / "missing.png")]
        with redirect_stdout(io.StringIO()) as out:
            bt_cli_verify.dispatch(ns, Path(self.tmp.name), "proj")
        self.assertIn("No puedo leer", out.getvalue())

    def test_the_panel_shows_the_images_under_the_note_and_the_form_takes_files(self):
        import bt_page_verification as page
        ctx = {"project": "proj", "rid": "REQ-009", "rdir": self.rdir, "token": "t"}
        html = page.panel(ctx, {"id": "SP-1"})
        self.assertIn('enctype="multipart/form-data"', html)
        self.assertIn('<input type="file" name="images" accept="image/png,image/jpeg,image/webp,image/gif" multiple', html)
        self.assertIn("Hasta 8 imágenes PNG, JPEG, WebP o GIF, 10 MB cada una y 30 MB en total", html)
        self.assertNotIn('class="pp-vthumbs" aria-label="Imágenes de tu rechazo"', html)
        v.decide("proj", self.rdir, "SP-1", "rejected", "se ve mal", attachments=[("a", PNG)])
        html = page.panel(ctx, {"id": "SP-1"})
        url = f"/p/proj/doc/requirements/REQ-009-demo/{self.entry()['attachments'][0]['path']}"
        self.assertIn(f'<img src="{url}" alt="Imagen 1 de tu rechazo"', html)
        self.assertLess(html.index("Tu nota: «se ve mal»"), html.index(url))
        self.projection(**{"SP-1": (2, "b" * 40)})                              # the repaired version: still shown
        html = page.panel(ctx, {"id": "SP-1"})
        self.assertIn("Rechazaste la versión 1", html)
        self.assertIn(url, html)


class Server(Base):
    """The real handler on a loopback port: the multipart form, the token and the image route."""

    def setUp(self):
        super().setUp()
        import bt_core
        import bt_server
        self.root = Path(self.tmp.name).resolve()
        self.rdir = self.root / "proj" / "requirements" / "REQ-009-demo"
        self.projection(**{"SP-1": (1, COMMIT)})
        for target, attr, value in ((bt_server, "ROOT", self.root), (bt_core, "ROOT", self.root),
                                    (bt_server, "STATE", self.root / ".state"), (bt_core, "STATE", self.root / ".state")):
            p = patch.object(target, attr, value)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(bt_server, "commit")
        self.commit = p.start()
        self.addCleanup(p.stop)
        self.token = bt_server.token()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), bt_server.Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def request(self, method, path, body=None, ctype=None):
        c = http.client.HTTPConnection("127.0.0.1", self.httpd.server_address[1], timeout=10)
        c.request(method, path, body=body, headers={"Content-Type": ctype} if ctype else {})
        r = c.getresponse()
        return r.status, r.getheader("Location") or "", r.getheader("Content-Type") or "", r.read(), dict(r.getheaders())

    def reject(self, files, token=None, comments="no carga"):
        ctype, body = multipart({"token": self.token if token is None else token, "anchor": "SP-1", "comments": comments},
                                files)
        return self.request("POST", "/p/proj/req/REQ-009/verify-reject", body, ctype)

    def test_the_form_rejects_with_images_and_the_panel_serves_them(self):
        status, location, *_ = self.reject([("images", "pantalla.png", PNG), ("images", "", b"")])
        self.assertEqual(status, 303)
        self.assertIn("SP-1%20rechazado", location)
        found = v._load(self.rdir)["subplans"]["SP-1"]["attachments"]
        self.assertEqual(len(found), 1)
        status, _, ctype, body, headers = self.request("GET", f"/p/proj/doc/requirements/REQ-009-demo/{found[0]['path']}")
        self.assertEqual((status, ctype, body), (200, "image/png", PNG))
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        (self.root / "proj" / "secret.png").write_bytes(PNG)                    # an image outside the folder: never
        for path in ("/p/proj/doc/requirements/REQ-009-demo/evidence/owner-rejected/SP-1-v1/..%2F..%2F..%2F..%2F..%2Fsecret.png",
                     "/p/proj/doc/secret.png"):
            self.assertEqual(self.request("GET", path)[0], 404, path)

    def test_a_bad_image_too_many_or_no_files_behave(self):
        status, location, *_ = self.reject([("images", "x.png", b"MZ\x90\x00 not an image")])
        self.assertEqual(status, 303)
        self.assertIn("no%20es%20una%20imagen", location)
        self.assertNotIn("SP-1", v._load(self.rdir)["subplans"])
        status, location, *_ = self.reject([("images", f"{i}.png", PNG) for i in range(9)])
        self.assertIn("Adjuntaste%209%20im%C3%A1genes", location)
        self.assertNotIn("SP-1", v._load(self.rdir)["subplans"])
        status, location, *_ = self.reject([])
        self.assertIn("SP-1%20rechazado", location)
        self.assertNotIn("attachments", v._load(self.rdir)["subplans"]["SP-1"])

    def test_the_token_is_still_required_and_an_oversized_body_is_refused_before_reading(self):
        self.assertEqual(self.reject([("images", "a.png", PNG)], token="wrong")[0], 403)
        self.assertNotIn("SP-1", v._load(self.rdir)["subplans"])
        with patch("bt_config.get", side_effect=lambda key, default=None: 1 if key.startswith("rejections.") else default):
            status, _, _, body, _ = self.reject([("images", "a.png", PNG + b"\x00" * (1024 * 1024 + images.FORM_OVERHEAD))])
        self.assertEqual(status, 413)
        self.assertIn("Las imágenes superan el máximo por rechazo", body.decode())
        ctype, body = multipart({"token": self.token, "anchor": "SP-1"}, [("images", "a.png", PNG)])
        self.assertEqual(self.request("POST", "/p/proj/req/REQ-009/verify-approve", body, ctype)[0], 403)   # only a rejection


class Brief(unittest.TestCase):
    """The Solucionador's trigger and brief name the images by absolute path, with the instruction to open them."""

    def test_the_brief_and_the_trigger_carry_the_images(self):
        import test_owner_reject_solver as owner
        case = owner.OwnerRejection("test_a_rejection_starts_the_solver_once_with_what_the_owner_saw_and_how_to_reproduce_it")
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.publish()
        v.decide("proj", case.rdir, "SP-1", "rejected", "El menú tapa el botón", attachments=[("a.png", PNG), ("b", JPG)])
        case.solver().run_pass([])
        (key, item), = case.owner_triggers().items()
        paths = [str(case.rdir.resolve() / a["path"]) for a in v._load(case.rdir)["subplans"]["SP-1"]["attachments"]]
        self.assertEqual(item["images"], paths)
        self.assertIn("with 2 image(s)", item["reason"])
        session = case.state()["sessions"][0]
        brief = (Path(session["dir"]) / "BRIEF.md").read_text()
        self.assertIn("The owner attached 2 image(s) to this rejection. Open every one with your image-reading tool", brief)
        for p in paths:
            self.assertIn(f"- `{p}`", brief)
        self.assertIn(f"`![Imagen 1 del rechazo](SP-1-v1/{Path(paths[0]).name})`", brief)
        self.assertIn("your request to the Planner lists every absolute image path", brief)
        self.assertLess(brief.index("El menú tapa el botón"), brief.index(paths[0]))
        v.decide("proj", case.rdir, "SP-1", "rejected", "El menú tapa el botón", attachments=[("c", GIF)])
        from bt_durable import rejections
        self.assertFalse(rejections.current(case.rdir, item))                   # same note, new images: a new trigger


if __name__ == "__main__":
    unittest.main()
