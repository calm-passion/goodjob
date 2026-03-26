import { a1 } from './index';

// 跨文件调用 + 回调 index.ts（双向跨文件引用）
export function a6(): void {
  a1();
}
