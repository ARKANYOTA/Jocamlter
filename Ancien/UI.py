from textual.app import App, ComposeResult
from textual import events
from textual.widgets import Static, Button, Input, Placeholder



import asyncio
class GLOBALS:
    COLORS = [
        "white",
        "maroon",
        "red",
        "purple",
        "fuchsia",
        "olive",
        "yellow",
        "navy",
        "teal",
        "aqua",
    ]

class UI(App):
    COLORS = GLOBALS.COLORS
    def on_enter(self, event: events.Enter) -> None:
        exit(0)

    def compose(self) -> ComposeResult:
        self.widget = Input(
            placeholder="Enter a color",
        )
        yield self.widget


    def on_mount(self) -> None:
        self.screen.styles.background = "darkblue"
        self.widget.styles.background = "red"
        self.width = "100%"
        self.height = "100%"

    def on_key(self, event: events.Key) -> None:
        if event.key.isdecimal():
            self.screen.styles.background = self.COLORS[int(event.key)]


if __name__ == "__main__":
    app = UI()
    app.run()
