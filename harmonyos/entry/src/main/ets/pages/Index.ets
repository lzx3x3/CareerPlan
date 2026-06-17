import { webview } from '@kit.ArkWeb';
import { preferences } from '@kit.ArkData';
import { BusinessError } from '@kit.BasicServicesKit';
import { SERVER_URL, PAGE_URL, STORAGE_KEYS } from '../utils/WebController';

@Entry
@Component
struct Index {
  // WebView 控制器
  private webController: webview.WebviewController = new webview.WebviewController();

  // 状态变量
  @State isLoading: boolean = true;
  @State loadProgress: number = 0;
  @State hasError: boolean = false;
  @State errorMsg: string = '';
  @State serverStatus: string = '检查中...';

  // 偏好存储（持久化 token 等）
  private prefStore: preferences.Preferences | null = null;

  aboutToAppear() {
    // 初始化本地存储
    try {
      preferences.getPreferences(getContext(), 'career_pref_store', (err, store) => {
        this.prefStore = store;
      });
    } catch (e) {
      hilog.warn(0x0000, 'CareerPlanner', 'Preferences init error');
    }
  }

  build() {
    Stack() {
      // ====== 1. WebView 主页面 ======
      Web({ src: PAGE_URL, controller: this.webController })
        .width('100%')
        .height('100%')
        .javaScriptAccess(true)
        .domStorageAccess(true)
        .geolocationAccess(true)
        .allowFileAccess(true)
        .imageAccess(true)
        .onlineImageAccessEnabled(true)
        .cacheMode(CacheMode.Default)
        .mixedMode(MixedMode.All)
        .zoomAccess(false)
        .overviewModeAccess(true)
        .databaseAccess(true)
        .onPageBegin((url) => {
          this.hasError = false;
          this.isLoading = true;
        })
        .onPageEnd((url) => {
          this.isLoading = false;
          this.loadProgress = 100;
        })
        .onProgressChange((progress) => {
          this.loadProgress = progress;
          if (progress >= 100) {
            this.isLoading = false;
          }
        })
        .onErrorReceive((event) => {
          this.hasError = true;
          this.errorMsg = event.errorInfo;
          this.isLoading = false;
        })
        .onHttpErrorReceive((event) => {
          hilog.warn(0x0000, 'CareerPlanner', 'HTTP error: ' + event.responseCode);
        })
        .onInterceptRequest((event) => {
          // 拦截本地 API 请求，转发到后端
          return null; // 允许直接访问
        })
        .onConfirm((event) => {
          // 处理 JS confirm 对话框
          return false;
        })
        .onAlert((event) => {
          // 处理 JS alert 对话框 - 用原生 Toast 代替
          AlertDialog.show({ message: event.message, confirm: { value: '确定' } });
          return true;
        })

      // ====== 2. 加载进度条 ======
      if (this.isLoading && this.loadProgress > 0 && this.loadProgress < 100) {
        ProgressBar({
          value: this.loadProgress,
          total: 100,
          style: ProgressStyle.Linear
        })
          .width('100%')
          .height(3)
          .position({ x: 0, y: 0 })
          .color($r('sys.color.ohos_id_color_primary'))
          .backgroundColor('#00000000');
      }

      // ====== 3. 加载中状态 ======
      if (this.isLoading && this.loadProgress === 0) {
        Column() {
          Image($r('app.media.app_icon'))
            .width(80)
            .height(80)
            .borderRadius(16)
            .margin({ bottom: 20 })
          Text('职画')
            .fontSize(24)
            .fontWeight(FontWeight.Bold)
            .fontColor('#4338ca')
          Text('智能职业规划助手')
            .fontSize(14)
            .fontColor('#888')
            .margin({ top: 6 })
          LoadingProgress()
            .width(36)
            .height(36)
            .margin({ top: 30 })
            .color('#6366f1')
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
        .backgroundColor('#f5f3ff');
      }

      // ====== 4. 错误页面 ======
      if (this.hasError) {
        Column() {
          Text('😕')
            .fontSize(64)
            .margin({ bottom: 16 })
          Text('连接失败')
            .fontSize(20)
            .fontWeight(FontWeight.Bold)
            .fontColor('#333')
            .margin({ bottom: 8 })
          Text('无法连接到服务器，请检查：')
            .fontSize(13)
            .fontColor('#888')
            .margin({ bottom: 16 })
          Column() {
            Text('• 后端服务是否已启动（python app.py）')
            Text('• 手机与电脑是否在同一网络')
            Text('• 服务器地址配置是否正确')
          }
          .fontSize(12)
          .fontColor('#666')
          .lineHeight(22)
          .margin({ bottom: 30 })

          Button('重新加载')
            .backgroundColor('#6366f1')
            .borderRadius(20)
            .width(160)
            .height(40)
            .onClick(() => {
              this.hasError = false;
              this.isLoading = true;
              this.loadProgress = 0;
              this.webController.refresh();
            })
        }
        .width('100%')
        .height('100%')
        .justifyContent(FlexAlign.Center)
        .alignItems(HorizontalAlign.Center)
        .backgroundColor('#f5f3ff')
        .padding(30);
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#f5f3ff')
    .expandSafeArea([SafeAreaType.SYSTEM], [SafeAreaEdge.TOP, SafeAreaEdge.BOTTOM]);
  }
}
