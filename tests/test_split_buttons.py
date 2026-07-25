"""Rendered-style regression tests for Thunderbird native split buttons."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THUNDERBIRD = Path("/Applications/Thunderbird Beta.app/Contents/MacOS/thunderbird")
SPEC = importlib.util.spec_from_file_location("liquidbird_demo", ROOT / "scripts/demo.py")
assert SPEC and SPEC.loader
demo = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = demo
SPEC.loader.exec_module(demo)


@unittest.skipUnless(
    os.environ.get("LIQUIDBIRD_UI_TESTS") == "1"
    and sys.platform == "darwin"
    and THUNDERBIRD.is_file(),
    "set LIQUIDBIRD_UI_TESTS=1 on macOS with Thunderbird Beta installed",
)
class SplitButtonIntegrationTest(unittest.TestCase):
    """Exercise LiquidBird against Thunderbird's generated XUL controls."""

    profile = ROOT / ".demo" / "split-button-test-profile"
    process: subprocess.Popen[bytes]
    client: demo.MarionetteClient

    @classmethod
    def setUpClass(cls) -> None:
        demo.prepare(cls.profile, date(2026, 7, 28))
        port = demo.reserve_loopback_port()
        environment = dict(os.environ)
        environment["MOZ_MARIONETTE"] = "1"
        environment["MOZ_MARIONETTE_PREF_STATE_ACROSS_RESTARTS"] = json.dumps(
            {"port": port}
        )
        cls.process = subprocess.Popen(
            demo.thunderbird_command(
                THUNDERBIRD,
                cls.profile,
                "mail",
                marionette=True,
            ),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=environment,
        )
        try:
            cls.client = demo.MarionetteClient(port, 40)
            cls.client.command(
                "WebDriver:NewSession",
                {"capabilities": {"alwaysMatch": {"acceptInsecureCerts": True}}},
            )
            cls.client.command("Marionette:SetContext", {"value": "chrome"})
        except Exception:
            demo.terminate_demo(cls.process)
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "client"):
            cls.client.close()
        if hasattr(cls, "process"):
            demo.terminate_demo(cls.process)
        marker = cls.profile / demo.PROFILE_MARKER
        if marker.is_file():
            shutil.rmtree(cls.profile)

    def split_button_styles(self, button_id: str) -> dict[str, object]:
        script = r"""
const [buttonId] = arguments;
const win = Services.wm.getMostRecentWindow("mail:3pane");
const pane = win?.document.getElementById("tabmail")?.currentTabInfo
  ?.chromeBrowser?.contentWindow;
if (!pane?.gDBView || pane.gDBView.rowCount < 1) {
  return null;
}
pane.threadTree.selectedIndex = 0;
const doc = pane.messageBrowser?.contentDocument;
const bar = doc?.getElementById("imip-bar");
const button = doc?.getElementById(buttonId);
const main = button?.querySelector(":scope > .toolbarbutton-menubutton-button");
const arrow = button?.querySelector(":scope > .toolbarbutton-menubutton-dropmarker");
if (!button || !main || !arrow) {
  return null;
}
bar?.removeAttribute("collapsed");
button.removeAttribute("hidden");
main.removeAttribute("hidden");
const pick = element => {
  const style = doc.defaultView.getComputedStyle(element);
  const rect = element.getBoundingClientRect();
  return {
    height: rect.height,
    overflow: style.overflow,
    padding: style.padding,
    borderTopWidth: style.borderTopWidth,
    borderInlineStartWidth: style.borderInlineStartWidth,
    borderRadius: style.borderRadius,
    backgroundColor: style.backgroundColor,
  };
};
const baseArrowBackground = doc.defaultView.getComputedStyle(arrow).backgroundColor;
button.setAttribute("open", "true");
arrow.getAnimations().forEach(animation => animation.finish());
const openArrowBackground = doc.defaultView.getComputedStyle(arrow).backgroundColor;
button.removeAttribute("open");
InspectorUtils.addPseudoClassLock(main, ":hover");
main.getAnimations().forEach(animation => animation.finish());
const hoverMainBackground = doc.defaultView.getComputedStyle(main).backgroundColor;
InspectorUtils.removePseudoClassLock(main, ":hover");
return {
  parent: pick(button),
  main: pick(main),
  arrow: pick(arrow),
  baseArrowBackground,
  openArrowBackground,
  hoverMainBackground,
};
"""
        deadline = time.monotonic() + 30
        while True:
            styles = self.client.command(
                "WebDriver:ExecuteScript",
                {
                    "script": script,
                    "args": [button_id],
                    "sandbox": "system",
                    "newSandbox": True,
                },
            )
            if isinstance(styles, dict):
                return styles
            if time.monotonic() >= deadline:
                self.fail(f"Thunderbird did not render split button {button_id}")
            time.sleep(0.25)

    def test_invitation_action_and_arrow_share_one_capsule(self) -> None:
        styles = self.split_button_styles("imipAcceptButton")

        self.assertEqual("clip", styles["parent"]["overflow"])
        self.assertEqual("0px", styles["parent"]["padding"])
        self.assertEqual("0px", styles["main"]["borderTopWidth"])
        self.assertEqual("0px", styles["main"]["borderRadius"])
        self.assertEqual("0px", styles["arrow"]["borderTopWidth"])
        self.assertEqual("1px", styles["arrow"]["borderInlineStartWidth"])
        self.assertEqual("0px", styles["arrow"]["borderRadius"])
        self.assertEqual(28, styles["parent"]["height"])
        self.assertEqual(26, styles["main"]["height"])
        self.assertEqual(styles["main"]["height"], styles["arrow"]["height"])

    def test_split_segments_expose_hover_and_open_feedback(self) -> None:
        styles = self.split_button_styles("imipAcceptButton")

        self.assertNotEqual(
            "rgba(0, 0, 0, 0)",
            styles["hoverMainBackground"],
        )
        self.assertNotEqual(
            styles["baseArrowBackground"],
            styles["openArrowBackground"],
        )

    def test_message_and_attachment_split_buttons_share_the_geometry(self) -> None:
        for button_id in ("hdrReplyAllButton", "attachmentSaveAllSingle"):
            with self.subTest(button_id=button_id):
                styles = self.split_button_styles(button_id)
                self.assertEqual("clip", styles["parent"]["overflow"])
                self.assertEqual("0px", styles["parent"]["padding"])
                self.assertEqual("0px", styles["main"]["borderTopWidth"])
                self.assertEqual("0px", styles["main"]["borderRadius"])
                self.assertEqual("0px", styles["arrow"]["borderTopWidth"])
                self.assertEqual(
                    "1px",
                    styles["arrow"]["borderInlineStartWidth"],
                )
                self.assertEqual("0px", styles["arrow"]["borderRadius"])


if __name__ == "__main__":
    unittest.main()
