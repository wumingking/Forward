from widget import show
import os

show(
    title=os.environ.get("MINIAPP_NAME", "MiniApp"),
    value="打开",
    subtitle="点击进入应用"
)