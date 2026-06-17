import { AbilityConstant, UIAbility, Want } from '@kit.AbilityKit';
import { window } from '@kit.ArkUI';
import { BusinessError } from '@kit.BasicServicesKit';

export default class EntryAbility extends UIAbility {
  private win: window.Window | null = null;

  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    // 应用初始化逻辑
    hilog.info(0x0000, 'CareerPlanner', 'Ability onCreate');
  }

  onDestroy(): void {
    hilog.info(0x0000, 'CareerPlanner', 'Ability onDestroy');
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    // 设置窗口全屏/沉浸式
    windowStage.getMainWindow().then((win) => {
      this.win = win;
      // 设置状态栏透明沉浸
      win.setWindowLayoutFullScreen(true).catch(() => {});
      // 设置状态栏文字颜色（浅色）
      win.setWindowSystemBarEnable(['status']).catch(() => {});
      win.setWindowSystemBarProperties({
        statusBarColor: '#00000000',
        isStatusBarLightIcon: true
      }).catch(() => {});
    }).catch((err: BusinessError) => {
      hilog.error(0x0000, 'CareerPlanner', 'Window stage error: ' + JSON.stringify(err));
    });

    // 加载主页面
    windowStage.loadContent('pages/Index', (err) => {
      if (err.code) {
        hilog.error(0x0000, 'CareerPlanner', 'Failed to load content: ' + JSON.stringify(err));
      }
    });
  }

  onWindowStageDestroy(): void {
    this.win = null;
  }

  onForeground(): void {
    hilog.info(0x0000, 'CareerPlanner', 'Ability onForeground');
  }

  onBackground(): void {
    hilog.info(0x0000, 'CareerPlanner', 'Ability onBackground');
  }
}
