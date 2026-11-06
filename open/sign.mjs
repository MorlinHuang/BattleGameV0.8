// 抖音直播小玩法「数据推送」签名（docs/抖音官方小玩法接入规范.md 第 7 节）：
//   除 x-signature、content-type 外的 x- 头按 key 字典序 k=v 用 & 连接，直接拼原始 body 字符串，再直接拼推送秘钥；
//   UTF-8 → MD5 原始 16 字节 → 标准 Base64。body 一定要用 HTTP 读到的原文，不能解析后再序列化。
import { createHash, timingSafeEqual } from 'node:crypto';

export const SIGN_HEADERS = ['x-msg-type', 'x-nonce-str', 'x-roomid', 'x-timestamp']; // 已按字典序

export function pushSignature(headers, rawBody, secret) {
  const kv = SIGN_HEADERS.map((k) => `${k}=${headers[k] ?? ''}`).join('&');
  return createHash('md5').update(Buffer.from(kv + rawBody + secret, 'utf8')).digest('base64');
}

export function verifyPush(headers, rawBody, secret) {
  const got = String(headers['x-signature'] || '');
  if (!got || !secret) return false;
  const want = pushSignature(headers, rawBody, secret);
  const a = Buffer.from(got), b = Buffer.from(want);
  return a.length === b.length && timingSafeEqual(a, b);
}

// 官方测试向量（启动时自检一次，算法被改坏立刻知道）
export function selfTest() {
  const h = { 'x-nonce-str': '123456', 'x-timestamp': '456789', 'x-roomid': '268', 'x-msg-type': 'live_gift' };
  return pushSignature(h, 'abc123你好', '123abc') === 'PDcKhdlsrKEJif6uMKD2dw==';
}
