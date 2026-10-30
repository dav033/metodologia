"""«Cómo probarlo»: concrete steps for a subplan version, generated from the plan (owner, 2026-10-30)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_verify_guide as guides

TABLE = "| Subplan | {w} | {h} | {e} |\n|---|---|---|---|\n"
SPEC = ("# Spec\n\n## Pruebas\nWhere to try it.\n\n" + TABLE.format(w="Where", h="How", e="Expect") +
        "| SP-1 | Local | 1) `npm run rag:migrate` then `npm run cuentas:sembrar-prueba` (type one password). 2) Open "
        "http://localhost:3000/3d. | 2) Sent to /login. |\n"
        "| SP-8 | Local Probar version | With SP-1's setup: 1) Open http://localhost:3000/login in English. 2) Sign in as "
        "master-designer@prueba.local and open the Taller. 3) Repeat step 2) on a phone. | 1) English. 2) No Spanish. "
        "3) Nothing overflows. |\n"
        "| SP-9 | Local | Run `npm run textos:sembrar`. As administrator open Textos. Reload. | Names in English. Codes stay. |\n"
        "| SP-5 | none | internal | |\n\n## Next\n")
SPEC_ES = ("# Spec\n\n## Pruebas\nDónde.\n\n" + TABLE.format(w="Dónde", h="Cómo", e="Resultado esperado") +
           "| SP-1 | Local | 1) `npm run rag:migrate` y luego `npm run cuentas:sembrar-prueba` (escriba una contraseña). "
           "2) Abra http://localhost:3000/3d. | 2) Se redirige a /login. |\n"
           "| SP-8 | Versión local de Probar | Con la configuración de SP-1: 1) Abra http://localhost:3000/login en inglés. "
           "2) Inicie sesión como master-designer@prueba.local y abra el Taller. 3) Repita el paso 2) en un teléfono. | "
           "1) Inglés. 2) Nada en español. 3) Nada se desborda. |\n\n## Siguiente\n")
PLAN = {"subplans": [{"id": "SP-5", "acceptance_criteria": ["Saved decorations reopen", "Others cannot edit them"]},
                     {"id": "SP-6", "ui": {"contract": "gasto-ia", "version": 1},
                      "acceptance_criteria": ["Spend is shown"]},
                     {"id": "SP-8"}],
        "tasks": [{"id": "T6.1", "subplan_id": "SP-6", "verification": [
            {"type": "command", "value": "npm test", "purpose": "unit"},
            {"type": "manual", "value": "Open Administración → Gasto and filter by user", "purpose": "Totals per user"}]}]}


class Guide(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-verify-guide-"))
        self.rdir = self.root / "proj" / "requirements" / "REQ-021-x"
        (self.rdir / "design" / "contracts").mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text(SPEC)
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN))

    def guide(self, sid, **kw):
        return guides.guide(self.root, "proj", self.rdir, sid, url="http://localhost:3002/", **kw)

    def test_numbered_items_pair_what_to_do_with_what_to_see_and_keep_an_inner_step_reference(self):
        lead, items = guides.numbered("Before: 1) Open it. 2) Sign in. 3) Repeat step 2) on a phone.")
        self.assertEqual(lead, "Before:")
        self.assertEqual(items, {1: "Open it.", 2: "Sign in.", 3: "Repeat step 2) on a phone."})
        g = self.guide("SP-8")
        self.assertEqual([s["expect"] for s in g["steps"]], ["English.", "No Spanish.", "Nothing overflows."])
        self.assertEqual(g["source"], "SPEC.md")

    def test_local_urls_become_the_versions_own_and_the_setup_of_another_subplan_comes_first(self):
        g = self.guide("SP-8")
        self.assertIn("http://localhost:3002/login", g["steps"][0]["do"])
        self.assertNotIn("3000", json.dumps(g))
        self.assertTrue(g["before"][0].startswith("Una sola vez, de SP-1: `npm run rag:migrate`"))

    def test_accounts_are_named_and_the_password_only_says_where_it_comes_from(self):
        g = self.guide("SP-8")
        self.assertEqual(g["accounts"], ["master-designer@prueba.local"])
        self.assertIn("`npm run cuentas:sembrar-prueba`", g["password"])
        g = self.guide("SP-8", recipe={"accounts": "Contraseñas en ~/dev/pictures/.env.local (ASESOR_E2E_*)."})
        self.assertEqual(g["password"], "Contraseñas en ~/dev/pictures/.env.local (ASESOR_E2E_*).")
        g = self.guide("SP-8", recipe={"prepare": [{"run": "npm run rag:migrate"}]})
        self.assertEqual(g["done"], ["«Probar» ya ejecuta `npm run rag:migrate` al arrancar."])

    def test_the_spanish_spec_is_preferred_when_it_has_the_same_rows(self):
        (self.rdir / "SPEC.es.md").write_text(SPEC_ES)
        g = self.guide("SP-8")
        self.assertEqual(g["source"], "SPEC.es.md")
        self.assertIn("Abra http://localhost:3002/login", g["steps"][0]["do"])
        self.assertEqual(g["steps"][2], {"do": "Repita el paso 2) en un teléfono.", "expect": "Nada se desborda."})
        self.assertTrue(g["before"][0].startswith("Una sola vez, de SP-1"))

    def test_a_paragraph_row_becomes_one_step_per_sentence_and_a_list_of_what_to_see(self):
        g = self.guide("SP-9", copy=Path("/v/SP-9-v1"))
        self.assertEqual([s["do"] for s in g["steps"]], ["Run `npm run textos:sembrar`.", "As administrator open Textos.",
                                                         "Reload."])
        self.assertEqual(g["expect"], ["Names in English.", "Codes stay."])
        self.assertEqual(g["commands"], "cd /v/SP-9-v1 && set -a && . /v/SP-9-v1.env && set +a")

    def test_without_a_row_the_plan_gives_manual_checks_then_acceptance_criteria(self):
        g = self.guide("SP-6")
        self.assertEqual(g["steps"], [{"do": "Open Administración → Gasto and filter by user", "expect": "Totals per user"}])
        self.assertEqual(g["source"], "PLAN.json")
        self.assertEqual(g["design"], {"ref": "gasto-ia@v1", "doc": ""})
        (self.rdir / "design" / "contracts" / "gasto-ia@v1.es.md").write_text("# diseño")
        self.assertEqual(self.guide("SP-6")["design"]["doc"], "requirements/REQ-021-x/design/contracts/gasto-ia@v1.es.md")
        g = self.guide("SP-5")
        self.assertEqual([s["do"] for s in g["steps"]], ["Comprueba: Saved decorations reopen",
                                                         "Comprueba: Others cannot edit them"])

    def test_at_most_eight_steps_and_the_rest_counted(self):
        many = " ".join(f"{n}) Step {n}." for n in range(1, 12))
        (self.rdir / "SPEC.md").write_text(SPEC.replace("| SP-9 | Local | Run", f"| SP-7 | Local | {many} | |\n| SP-9 | Local | Run"))
        g = self.guide("SP-7")
        self.assertEqual((len(g["steps"]), g["more"]), (8, 3))

    def test_the_same_files_give_the_same_guide(self):
        self.assertEqual(self.guide("SP-8"), self.guide("SP-8"))


class SignedIn(unittest.TestCase):
    """D-211: with automatic sign-in the guide never asks for a password or an account the test database lacks."""
    ACCOUNTS = ["test+administrador@req021.test", "test+designer_plus@req021.test", "test+master_designer@req021.test"]

    def test_a_sign_in_step_names_the_seeded_account_to_pick(self):
        import bt_verify_guide as guides
        said = guides.signed_in("Ejecuta `npm run dev`, abre http://localhost:3001/login e inicia sesión como admin@prueba.local.",
                                self.ACCOUNTS)
        self.assertEqual(said, "Ejecuta `npm run dev`, abre http://localhost:3001/login (ya entras con sesión iniciada; "
                               "en «Entras como» elige test+administrador@req021.test).")
        self.assertEqual(guides.test_account("designer-plus@prueba.local", self.ACCOUNTS), "test+designer_plus@req021.test")
        self.assertEqual(guides.test_account("master-designer@x", self.ACCOUNTS), "test+master_designer@req021.test")
        self.assertEqual(guides.test_account("nadie@x.test", self.ACCOUNTS), "nadie@x.test")

    # D-231: roles and aliases come from the recipe, not from code
    SHOP: ClassVar[list] = [{"email": "qa+owner@shop.test", "role": "owner", "label": "Dueño", "aliases": ["admin", "store-manager"]},
            {"email": "qa+clerk@shop.test", "role": "clerk", "label": "Cajero"},
            {"email": "qa+night_clerk@shop.test", "role": "night_clerk"}]

    def test_plan_accounts_map_through_the_recipes_roles_and_aliases(self):
        self.assertFalse(hasattr(guides, "_ROLE_ALIAS"))
        self.assertEqual(guides.test_account("admin@prueba.local", self.SHOP), "qa+owner@shop.test")
        self.assertEqual(guides.test_account("Store_Manager@x", self.SHOP), "qa+owner@shop.test")
        self.assertEqual(guides.test_account("CLERK@x", self.SHOP), "qa+clerk@shop.test")
        self.assertEqual(guides.test_account("night-clerk@x", self.SHOP), "qa+night_clerk@shop.test")
        self.assertEqual(guides.test_account("cajero@x", self.SHOP), "qa+clerk@shop.test")       # its label
        self.assertEqual(guides.test_account("nadie@x.test", self.SHOP), "nadie@x.test")
        self.assertEqual(guides.test_account("night@x", self.SHOP), "qa+night_clerk@shop.test")  # one role starts so
        self.assertEqual(guides.test_account("n@x", self.SHOP), "n@x")                          # too short to guess

    def test_the_guide_and_the_manual_card_name_the_recipes_accounts(self):
        root = Path(tempfile.mkdtemp(prefix="bt-verify-guide-"))
        rdir = root / "shop" / "requirements" / "REQ-002-x"
        rdir.mkdir(parents=True)
        (rdir / "SPEC.md").write_text("# Spec\n\n## Pruebas\n\n" + TABLE.format(w="Where", h="How", e="Expect") +
                                      "| SP-1 | Local | 1) Open http://localhost:3000/till and sign in as clerk@shop.local. "
                                      "| 1) The till opens. |\n\n## Next\n")
        (rdir / "PLAN.json").write_text(json.dumps({"tasks": [{"id": "T1.1", "subplan_id": "SP-1", "verification": [
            {"type": "manual", "value": "As Cajero, close the till", "purpose": "Totals match"}]}]}))
        recipe = {"auto_login": {"cookie": "sid", "mint": "x", "default": "qa+owner@shop.test", "accounts": self.SHOP}}
        g = guides.guide(root, "shop", rdir, "SP-1", url="http://localhost:3005/", recipe=recipe)
        self.assertIn("elige qa+clerk@shop.test", g["steps"][0]["do"])
        self.assertEqual((g["accounts"], g["password"], g["signed"]), (["qa+clerk@shop.test"], "", "qa+owner@shop.test"))
        card = guides.manual(root, "shop", rdir, "T1.1", url="http://localhost:3005/", recipe=recipe)
        self.assertEqual(card["accounts"], ["qa+clerk@shop.test"])                                # «As Cajero»: its label


if __name__ == "__main__":
    unittest.main()
