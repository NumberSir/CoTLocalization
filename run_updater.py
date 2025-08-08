import argparse
import getpass
from game_updater import main
from game_updater.config import STABLE_GAME_ID, EARLY_ACCESS_GAME_ID

def run():
    parser = argparse.ArgumentParser(
        description="游戏更新和故事导出自动化工具。"
    )
    parser.add_argument(
        "--ea",
        action="store_true",
        help="如果设置此标志，将更新抢先体验版。否则，将更新稳定版。"
    )
    args = parser.parse_args()

    if args.ea:
        print("已选择抢先体验版更新流程。")
        password = getpass.getpass("请输入抢先体验版的密码: ")
        main.run_update_and_export(EARLY_ACCESS_GAME_ID, password)
    else:
        print("已选择稳定版更新流程。")
        main.run_update_and_export(STABLE_GAME_ID)

if __name__ == "__main__":
    run()