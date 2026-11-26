"""AVYX Calculator."""
import ast
import operator
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from .. import appkit, config  # noqa: E402
from ..appkit import AppWindow  # noqa: E402

px = config.px
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Mod: operator.mod}


def evaluate(expr):
    """Safe arithmetic evaluation (numbers, + - * / %, unary minus, parentheses)."""
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        raise ValueError("bad expression")
    return ev(ast.parse(expr, mode="eval"))


def fmt(v):
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return "Error"
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
        s = ("%.10f" % v).rstrip("0").rstrip(".")
        return s if len(s) <= 16 else "%.10g" % v
    return str(v)


class CalcWindow(AppWindow):
    LAYOUT = [["AC", "±", "%", "÷"], ["7", "8", "9", "×"], ["4", "5", "6", "−"], ["1", "2", "3", "+"], ["0", ".", "⌫", "="]]

    def __init__(self, app):
        super().__init__(app, "Calculator", 340, 540)
        self.add_css_class("calc")
        self.expr = ""
        self.result_shown = False
        spacer = Gtk.Box(hexpand=True)
        self.header_append(spacer)
        self.expr_l = Gtk.Label(xalign=1)
        self.expr_l.add_css_class("calc-expr")
        self.disp = Gtk.Label(label="0", xalign=1)
        self.disp.add_css_class("calc-display")
        self.disp.set_ellipsize(1)
        self.body.append(self.expr_l)
        self.body.append(self.disp)
        grid = Gtk.Grid(row_spacing=px(10), column_spacing=px(10), column_homogeneous=True, row_homogeneous=True)
        for m in ("start", "end", "bottom"):
            getattr(grid, "set_margin_" + m)(px(16))
        grid.set_vexpand(True)
        for r, rowk in enumerate(self.LAYOUT):
            for c, k in enumerate(rowk):
                b = Gtk.Button(label=k)
                b.add_css_class("key")
                if k in "÷×−+=":
                    b.add_css_class("op")
                elif k in ("AC", "±", "%", "⌫"):
                    b.add_css_class("fn")
                b.connect("clicked", lambda _b, kk=k: self.press(kk))
                grid.attach(b, c, r, 1, 1)
        self.body.append(grid)
        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._key)
        self.add_controller(key)

    def _show(self):
        self.disp.set_label(self.expr or "0")

    def press(self, k):
        if k == "AC":
            self.expr = ""
            self.expr_l.set_label("")
            self.result_shown = False
        elif k == "⌫":
            self.expr = self.expr[:-1]
        elif k == "±":
            if self.expr.startswith("−"):
                self.expr = self.expr[1:]
            elif self.expr:
                self.expr = "−" + self.expr
        elif k == "=":
            self.calculate()
            return
        elif k in "÷×−+%":
            if self.result_shown:
                self.result_shown = False
            if self.expr and self.expr[-1] in "÷×−+%":
                self.expr = self.expr[:-1]
            if self.expr or k == "−":
                self.expr += k
        else:
            if self.result_shown:
                self.expr = ""
                self.result_shown = False
            if k == "." and self.expr and (self.expr.split("÷")[-1].split("×")[-1].split("−")[-1].split("+")[-1].split("%")[-1]).count("."):
                return
            self.expr += k
        self._show()

    def calculate(self):
        if not self.expr:
            return
        e = self.expr.replace("÷", "/").replace("×", "*").replace("−", "-")
        try:
            val = evaluate(e)
            out = fmt(val)
        except ZeroDivisionError:
            out = "Can't divide by zero"
        except (ValueError, SyntaxError, OverflowError):
            out = "Error"
        self.expr_l.set_label(self.expr + " =")
        self.expr = out.replace("-", "−") if out[:1].isdigit() or out[:1] == "-" else ""
        self.disp.set_label(out)
        self.result_shown = bool(self.expr)

    def _key(self, ctl, keyval, keycode, state):
        ch = Gdk.keyval_to_unicode(keyval)
        c = chr(ch) if ch else ""
        if c.isdigit() or c == ".":
            self.press(c)
        elif c in "+%":
            self.press(c)
        elif c == "-":
            self.press("−")
        elif c == "*":
            self.press("×")
        elif c == "/":
            self.press("÷")
        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) or c == "=":
            self.press("=")
        elif keyval == Gdk.KEY_BackSpace:
            self.press("⌫")
        elif keyval == Gdk.KEY_Escape:
            self.press("AC")
        else:
            return False
        return True


class CalcApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.avyx.Calculator")

    def do_startup(self):
        Gtk.Application.do_startup(self)
        appkit.setup_env()

    def do_activate(self):
        w = self.get_active_window()
        (w or CalcWindow(self)).present()


def main(argv):
    return CalcApp().run(argv)
