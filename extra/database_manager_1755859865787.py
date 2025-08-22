import keyboard
import time

def test_hotkey_availability(hotkey):
    """
    测试快捷键是否可用（可能被其他程序占用）
    :param hotkey: 要测试的快捷键组合
    """
    try:
        print(f"测试快捷键: {hotkey}")
        # 尝试注册快捷键
        keyboard.add_hotkey(hotkey, lambda: print(f"{hotkey} 被触发"))
        print(f"快捷键 {hotkey} 注册成功，可能未被占用")
        # 移除测试的快捷键
        keyboard.remove_hotkey(hotkey)
        return True
    except Exception as e:
        print(f"快捷键 {hotkey} 可能已被占用: {e}")
        return False

def check_common_hotkeys():
    """
    检查常见快捷键的可用性
    """
    common_hotkeys = [
        'ctrl+shift+enter',
        'ctrl+alt+L',
        'ctrl+space',
        'alt+f1',
        'ctrl+1',
        'ctrl+2'
    ]

    print("检查常见快捷键可用性:")
    for hotkey in common_hotkeys:
        test_hotkey_availability(hotkey)
        time.sleep(0.1)  # 短暂延迟避免过快操作

# 修复：添加缺失的函数定义
def check_key_conflicts():
    """
    检查键盘快捷键冲突的示例函数
    """
    print("keyboard模块功能信息:")
    print("1. keyboard模块主要用于:")
    print("   - 监听键盘事件")
    print("   - 发送键盘事件")
    print("   - 注册快捷键回调函数")
    print("\n2. 常用方法:")
    methods = [attr for attr in dir(keyboard) if not attr.startswith('_') and callable(getattr(keyboard, attr))]
    for method in methods[:10]:  # 只显示前10个方法
        print(f"   - {method}")

    print(f"\n3. 总共找到 {len(methods)} 个可用方法")

# 使用示例
if __name__ == "__main__":
    check_key_conflicts()
    print("\n" + "="*50)
    check_common_hotkeys()
