import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import bt_page_planning_asks as asks
import bt_planning_notes as notes
import bt_rounds as rounds

ROUND = {"title": "SP-1 questions", "intro": "Hello", "questions": [
    {"id": "q1", "text": "Plans and roles?", "type": "choice", "options": [{"key": "a", "label": "Plans are permission sets"},
                                                                          {"key": "b", "label": "Other"}], "recommended": "a"},
    {"id": "q2", "text": "Session length?", "type": "open", "suggested": "30 days"}]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "REQ-021-demo"
        self.rdir.mkdir()
        self.ctx = {"project": "pictures", "rid": "REQ-021", "rdir": self.rdir, "token": "tok", "opts": {"sp": "SP-1", "lang": "es", "mode": "subplans", "view": "asks", "rev": 0, "only": False, "filter": ""}}


class OpenRound(Base):
    def test_no_open_round_means_a_hidden_block_outside_the_asks_view(self):
        quiet = {**self.ctx, "opts": {**self.ctx["opts"], "view": "design"}}
        self.assertIn("hidden", asks.asks(quiet))
        f = rounds.new_round(self.rdir, dict(ROUND))
        rounds.answer_round(f, {"q1": {"choice": "a"}, "q2": {"text": "x"}}, "web")
        self.assertIn("hidden", asks.asks(quiet))

    def test_the_asks_view_without_an_open_round_says_so_instead_of_showing_something_else(self):
        html = asks.asks(self.ctx)                                  # ctx view is «asks»
        self.assertIn("No hay preguntas abiertas", html)
        self.assertIn("view=notes", html)
        self.assertIn("Volver al subplan SP-1", html)

    def test_the_open_round_is_a_form_that_returns_to_the_subplan_view(self):
        rounds.new_round(self.rdir, dict(ROUND))
        html = asks.asks(self.ctx)
        for expected in ("El Planner te pregunta", "Ronda 1 · 2 preguntas", "Plans and roles?", 'name="back" value="plan"',
                         'name="back_sp" value="SP-1"', "/p/pictures/req/REQ-021/answer", "30 days", "checked",
                         "Recomendada", "Volver al subplan SP-1", 'name="q1" value="a"', 'name="q1__note"', 'name="q2"', "Enviar respuestas"):
            self.assertIn(expected, html)
        self.assertEqual(html, asks.asks(self.ctx))            # stable: the live refresh does not swap it while typing

    def test_long_texts_are_cut_at_a_clause_or_a_word_never_mid_word(self):
        first = "Una primera frase lo bastante larga como para ser un buen titular de la pregunta y no un recorte tonto."
        head, rest = asks._clip(first + " " + "palabra " * 60)
        self.assertEqual(head, first)
        self.assertTrue(rest.startswith("palabra"))
        head, rest = asks._clip("x " * 300)
        self.assertTrue(head.endswith("…"))
        self.assertEqual(asks._clip("corto"), ("corto", ""))

    def test_notes_and_past_rounds_have_a_tab(self):
        self.assertIn("Todavía no ha guardado notas", asks.panel(self.ctx))
        notes.add(self.rdir, "Routes guarded only by proxy.ts", "finding")
        f = rounds.new_round(self.rdir, dict(ROUND))
        rounds.answer_round(f, {"q1": {"choice": "a", "note": "ok"}, "q2": {"text": "30 days"}}, "web")
        html = asks.panel(self.ctx)
        self.assertIn("Routes guarded only by proxy.ts", html)
        self.assertIn("Ronda 1", html)
        self.assertIn("Plans are permission sets", html)
        self.assertEqual(asks.tab_label(self.ctx), "Notas y rondas · 1/1")


class WebActions(Base):
    def test_answering_wakes_the_planner_and_planning_actions_do_too(self):
        import bt_server
        f = rounds.new_round(self.rdir, dict(ROUND))
        stub = SimpleNamespace(tell_planner=Mock())
        with patch.object(bt_server, "commit"):
            msg = bt_server.Handler.answer(stub, "pictures", "REQ-021", self.rdir,
                                           {"round": f.name, "q1": "a", "q1__note": "", "q2": "30 days"})
        self.assertIn("Respuestas guardadas", msg)
        stub.tell_planner.assert_called_once()
        self.assertIn("round 1 of REQ-021", stub.tell_planner.call_args.args[2])
        self.assertEqual(rounds.load(f)["status"], "answered")

    def test_notify_planner_types_only_into_a_running_planner(self):
        import bt_agent_terminal as terminal
        with patch("bt_agent_terminal.exists", return_value=False), patch("bt_agent_terminal.send") as send:
            self.assertFalse(terminal.notify_planner("pictures", "REQ-021", "hi"))
            send.assert_not_called()
        with patch("bt_agent_terminal.exists", return_value=True), patch("bt_agent_terminal.send", return_value="Enviado.") as send:
            self.assertTrue(terminal.notify_planner("pictures", "REQ-021", "hi"))
            self.assertIn("Automatic notice from the web", send.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
