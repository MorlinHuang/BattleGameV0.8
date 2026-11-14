// 查手机 · 官方礼物 / 评论 / 点赞 → 游戏里的七档礼物（main.js SHOP 的键）。改映射只改这个文件；
// 直播画面开连时从 GET /api/open/gifts 取同一份（web/open.js），模拟推送工具 tools/open-mock.mjs 也从这里取。
// 官方礼物名、抖币价、sec_gift_id 照抄美食大赛 server/open/gifts.mjs（抖音开放平台「直播间礼物互动能力」第四节，2026-10-22 查）。
//
//   点赞    = 直播间点赞推送 live_like，like_num 个算 like_num 份（SHOP.like）
//   666     = 评论指令（不是礼物）：评论里含 666 → main.js comment() 给本方一份 SHOP.six（免费）
//   站队    = 评论 1 / 2（加入小美 / 大帅）
//   付费 5 种：仙女棒 1 / 魔法镜 19 / 甜甜圈 52 / 能量电池 99 / 派对话筒 299 抖币（官方上限 8 种，后台「营收 → 礼物评论配置」里选这 5 种）
// 「假设」：开放平台后台给的 sec_gift_id 和这份表一致；拿到后台截图再核一遍。
export const PAID = [
  { key: 'wand',    name: '仙女棒',   diamond: 1,   id: 'n1/Dg1905sj1FyoBlQBvmbaDZFBNaKuKZH6zxHkv8Lg5x2cRfrKUTb8gzMs=' },
  { key: 'mirror',  name: '魔法镜',   diamond: 19,  id: 'fJs8HKQ0xlPRixn8JAUiL2gFRiLD9S6IFCFdvZODSnhyo9YN8q7xUuVVyZI=' },
  { key: 'donut',   name: '甜甜圈',   diamond: 52,  id: 'PJ0FFeaDzXUreuUBZH6Hs+b56Jh0tQjrq0bIrrlZmv13GSAL9Q1hf59fjGk=' },
  { key: 'battery', name: '能量电池', diamond: 99,  id: 'IkkadLfz7O/a5UR45p/OOCCG6ewAWVbsuzR/Z+v1v76CBU+mTG/wPjqdpfg=' },
  { key: 'mic',     name: '派对话筒', diamond: 299, id: 'YbLESoUj053FWVYPWUNOAtp4FYnb+/eZbyrLi7ndArVFz14rivgxf0cFrKs=' },
];
// 后台「评论关键词」（官方：只推送含关键词的评论，最多 10 个）
export const COMMENT_KEYWORDS = ['1', '2', '666'];
export const FEN_PER_DIAMOND = 10;   // 推送 gift_value 单位是分；1 抖币 = 10 分（假设，只用于模拟推送和日志核对）
export const giftById = (id) => PAID.find((g) => g.id === String(id || ''));
export const findGift = (s) => PAID.find((g) => g.name === s || g.key === s || g.id === s);
// 给直播画面的那份（不带价格以外的东西）
export const table = () => ({ paid: PAID.map(({ key, name, diamond, id }) => ({ key, name, diamond, id })), keywords: COMMENT_KEYWORDS });
