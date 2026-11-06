// 抖音开放平台「直播小玩法」服务端接口（开发者服务端调用；appid / AppSecret 只能放服务端）。
// 接口、参数、返回字段照 docs/抖音官方小玩法接入规范.md 第 3～5、9、10 节。
// 本玩法用到的四类推送（11-01 加粉丝团：加团 / 升级出「点亮灯牌」，要后台开通「直播间粉丝团互动数据」能力；没开通这一类任务起不来，别的三类照常）
export const MSG_TYPES = ['live_comment', 'live_gift', 'live_like', 'live_fansclub'];

const TOKEN_URL = 'https://developer.toutiao.com/api/apps/v2/token';
const WEBCAST = 'https://webcast.bytedance.com';

// room_id 是超过 2^53 的整数：解析前先改成字符串，不然丢精度
const parse = (text) => JSON.parse(text.replace(/"(room_id|roomid)"\s*:\s*(\d+)/g, '"$1":"$2"'));

export class OpenApi {
  constructor({ appid, appSecret, fetchImpl = fetch, log = () => {} }) {
    this.appid = appid; this.appSecret = appSecret; this.fetch = fetchImpl; this.log = log;
    this.token = ''; this.tokenAt = 0; this.tokenTask = null;
  }

  async req(method, url, { headers = {}, body, query } = {}) {
    const u = new URL(url);
    for (const [k, v] of Object.entries(query || {})) u.searchParams.set(k, String(v));
    const r = await this.fetch(u, { method, headers: { 'content-type': 'application/json', ...headers }, body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(8000) });
    const text = await r.text();
    let j;
    try { j = parse(text); } catch { throw new Error(`${u.pathname} 返回不是 JSON（HTTP ${r.status}）`); }
    return j;
  }

  // access_token：有效 2 小时；重新获取会让上一个 5 分钟后失效，所以整个服务共用一个、每小时换一次（并发调用只换一次）
  async accessToken() {
    if (this.token && Date.now() - this.tokenAt < 3600e3) return this.token;
    this.tokenTask ||= (async () => {
      try {
        const j = await this.req('POST', TOKEN_URL, { body: { appid: this.appid, secret: this.appSecret, grant_type: 'client_credential' } });
        if (j.err_no !== 0 || !j.data?.access_token) throw new Error(`取 access_token 失败：${j.err_no} ${j.err_tips || ''}`);
        this.token = j.data.access_token; this.tokenAt = Date.now();
        return this.token;
      } finally { this.tokenTask = null; }
    })();
    return this.tokenTask;
  }

  // 直播伴侣传给玩法的启动 token（30 分钟有效）→ 直播间信息
  async roomInfo(launchToken) {
    const j = await this.req('POST', WEBCAST + '/api/webcastmate/info', { headers: { 'x-token': await this.accessToken() }, body: { token: launchToken } });
    const info = j.data?.info;
    if (!info?.room_id) throw new Error(`用启动参数换直播间失败：${j.err_no ?? j.errcode ?? ''} ${j.err_msg || j.errmsg || j.err_tips || ''}`.trim());
    return { roomId: String(info.room_id), anchor: { openId: info.anchor_open_id || '', name: info.nick_name || '', avatar: info.avatar_url || '' } };
  }

  async task(action, roomId, msgType) {
    const headers = { 'access-token': await this.accessToken() };
    const params = { roomid: roomId, appid: this.appid, msg_type: msgType };
    const j = action === 'get'
      ? await this.req('GET', WEBCAST + '/api/live_data/task/get', { headers, query: params })
      : await this.req('POST', WEBCAST + `/api/live_data/task/${action}`, { headers, body: params });
    if (j.err_no !== 0) throw new Error(`${msgType} 推送任务 ${action} 失败：${j.err_no} ${j.err_msg || ''}`);
    return j.data || {};
  }
  startTask(roomId, msgType) { return this.task('start', roomId, msgType); }
  stopTask(roomId, msgType) { return this.task('stop', roomId, msgType); }
  async taskStatus(roomId, msgType) { return (await this.task('get', roomId, msgType)).status; } // 1 不存在 2 未启动 3 运行中

  // 推送失败的礼物数据（约 24 小时、10 万条；没有确认机制，靠 msg_id 去重）
  async failData(roomId, msgType, pageNum, pageSize = 100) {
    const j = await this.req('GET', WEBCAST + '/api/live_data/task/fail_data/get', { headers: { 'access-token': await this.accessToken() }, query: { roomid: roomId, appid: this.appid, msg_type: msgType, page_num: pageNum, page_size: pageSize } });
    if (j.err_no !== 0) throw new Error(`失败数据查询出错：${j.err_no} ${j.err_msg || ''}`);
    return j.data || { data_list: [] };
  }

  // 履约上报：ack_type 1 收到推送 / 2 处理完成。注意这个接口参数名是 app_id / room_id（带下划线）
  async ack(roomId, ackType, items) {
    const data = JSON.stringify(items.map((i) => ({ msg_id: i.msgId, msg_type: i.msgType, client_time: i.at })));
    const j = await this.req('POST', WEBCAST + '/api/live_data/ack', { headers: { 'access-token': await this.accessToken() }, body: { ack_type: ackType, app_id: this.appid, room_id: roomId, data } });
    if (j.err_no !== 0) this.log(`履约上报失败：${j.err_no} ${j.err_msg || ''}`);
  }
}
