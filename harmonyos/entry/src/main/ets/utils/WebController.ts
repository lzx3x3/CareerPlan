/**
 * 职画 - WebView 控制器工具
 * 管理 WebView 与原生能力的桥接
 */

// 后端服务器地址（部署时替换为实际地址）
// 开发环境使用局域网 IP，生产环境使用域名
export const SERVER_URL = 'http://localhost:5000';

// 前端页面地址（通常是 server/ 下同域访问）
export const PAGE_URL = SERVER_URL + '/';

// 检查网络连接状态
export function isNetworkAvailable(): boolean {
  // HarmonyOS 网络连接检查
  // 实际项目中使用 @kit.NetworkKit 检测
  return true;
}

// 本地存储 Key
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'career_token',
  USER_DATA: 'career_user',
  CACHE_PREFIX: 'career_cache_',
  LAST_SYNC: 'last_sync_time',
};

// 错误处理
export function handleWebError(errorCode: number, description: string): string {
  const messages: Record<number, string> = {
    [-1]: '未知加载错误',
    [-2]: '服务器连接超时',
    [-3]: '无法连接到服务器',
    [-4]: '页面加载失败',
  };
  return messages[errorCode] || `加载错误(${errorCode}): ${description}`;
}

// 生成缓存键
export function getCacheKey(key: string): string {
  return STORAGE_KEYS.CACHE_PREFIX + key;
}
