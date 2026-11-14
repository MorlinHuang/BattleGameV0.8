// 玩法客户端（exe）这一侧：把直播伴侣给的启动 token 交给开发者服务端，再用长连接收这个直播间的事件。
// appid / AppSecret 不在 exe 里：换直播间、开推送任务、验推送签名都在开发者服务端做（hub.mjs）。
// 事件流是 Server-Sent Events，断线后带上次收到的 seq 续上（服务端留最近 600 条），不丢不重。
// seq 是服务端进程内的序号：连上的是重启过的新进程（boot 变了），序号从头算。
import { EventEmitter } from 'node:events';

export class RemoteLink extends EventEmitter {
  constructor({ server, log = console.log }) {
    super();
    this.server = String(server || '').replace(/\/+$/, '');
    this.log = log;
    this.room = null; // {roomId, anchor, tasks, real, ticket}
    this.lastSeq = -1;
    this.boot = ''; // lastSeq 所属的服务端进程
    this.state = { status: '未启动', warn: '' };
    this.ctl = null;
    this.closed = false;
  }
  setState(status, warn = '') { this.state = { status, warn }; this.emit('status', this.state); }

  async launch(token) {
    if (!this.server) throw new Error('没有配置开发者服务端地址（config.json 的 openServer）');
    this.setState('正在连接直播间…');
    let j;
    try {
      const r = await fetch(this.server + '/api/open/launch', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ token }), signal: AbortSignal.timeout(15000) });
      j = await r.json();
      if (!r.ok) throw new Error(j.error || 'HTTP ' + r.status);
    } catch (e) { this.setState('连接失败', e.message); throw e; }
    this.room = j; this.lastSeq = -1; this.boot = ''; this.closed = false;
    this.emit('room', j);
    this.listen();
    return j;
  }

  async listen() {
    let wait = 1000;
    while (!this.closed && this.room) {
      const { roomId, ticket } = this.room;
      this.ctl = new AbortController();
      try {
        const r = await fetch(`${this.server}/api/open/events?room=${encodeURIComponent(roomId)}&ticket=${encodeURIComponent(ticket)}&since=${this.lastSeq}&boot=${encodeURIComponent(this.boot)}`, { signal: this.ctl.signal });
        if (r.status === 403) { this.setState('连接失败', '服务端不认这个直播间凭证'); return; }
        if (!r.ok || !r.body) throw new Error('HTTP ' + r.status);
        this.setState('已连接');
        wait = 1000;
        const reader = r.body.getReader(), dec = new TextDecoder();
        let buf = '';
        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          buf += dec.decode(value, { stream: true });
          let i;
          while ((i = buf.indexOf('\n\n')) >= 0) {
            const block = buf.slice(0, i); buf = buf.slice(i + 2);
            let event = 'message', data = '';
            for (const line of block.split('\n')) { if (line.startsWith('event:')) event = line.slice(6).trim(); else if (line.startsWith('data:')) data += line.slice(5).trim(); }
            if (!data) continue;
            const d = JSON.parse(data);
            if (event === 'room') {
              // 首次连上：从现在开始收；连上的是新进程：服务端会从它的第 1 条补发
              if (d.boot !== this.boot) { this.lastSeq = this.lastSeq < 0 ? d.seq : 0; this.boot = d.boot; }
              this.room = { ...this.room, ...d, ticket: this.room.ticket }; this.emit('room', this.room); }
            else if (d.seq > this.lastSeq) { this.lastSeq = d.seq; this.emit('event', d); }
          }
        }
        throw new Error('连接断开');
      } catch (e) {
        if (this.closed) return;
        this.setState('重连中…', e.message);
        await new Promise((ok) => setTimeout(ok, wait));
        wait = Math.min(wait * 2, 10000);
      }
    }
  }

  async close() {
    this.closed = true; this.ctl?.abort();
    this.setState('未启动');
  }
}
