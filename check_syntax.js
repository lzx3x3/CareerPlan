
// ============================================================
//  ===== 全局状态 =====
// ============================================================
const state = {
  step: 0,
  avatar: '🧑‍🎓',
  coins: 0,
  achievements: [],   // {time, title, icon}
  powerup: false,     // 蘑菇加倍
  soundOn: true,
  milestones: [],     // 路标数据
  checkedNodes: {},   // {nodeId: {note, extra, time}}
  sel: { industry:[], job:[], company:[], city:[], goal:[], eng:[], skill:[] },
  mbti: { answers:{}, result:null, q:0 },
  form: {},           // 简历保留数据
};

// ============================================================
//  ===== Web Audio BGM (马里奥风格合成) =====
// ============================================================
let audioCtx = null;
let bgmNodes = [];
let bgmLoop = null;

function ensureAudio() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
}

// 马里奥主题旋律近似音符 (频率Hz, 时值s)
const marioMelody = [
  [659,0.15],[659,0.15],[0,0.08],[659,0.15],[0,0.08],[523,0.15],[659,0.18],
  [784,0.18],[0,0.18],[392,0.18],[0,0.18],
  [523,0.15],[0,0.1],[392,0.15],[0,0.1],[330,0.15],[0,0.1],
  [440,0.18],[494,0.18],[466,0.15],[440,0.18],
  [392,0.15],[659,0.15],[784,0.15],[880,0.18],[698,0.15],[784,0.15],
  [659,0.18],[523,0.15],[587,0.15],[494,0.18],[0,0.2],
];

let bgmPlaying = false;
let bgmTimeoutId = null;

function playBGM() {
  if (!state.soundOn || bgmPlaying) return;
  ensureAudio();
  bgmPlaying = true;
  let t = audioCtx.currentTime + 0.05;
  function scheduleLoop() {
    marioMelody.forEach(([freq, dur]) => {
      if (freq > 0) {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain); gain.connect(audioCtx.destination);
        osc.type = 'square';
        osc.frequency.setValueAtTime(freq, t);
        gain.gain.setValueAtTime(0.08, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + dur * 0.9);
        osc.start(t); osc.stop(t + dur);
      }
      t += dur;
    });
    // 循环
    const loopDur = marioMelody.reduce((s,[,d])=>s+d,0);
    bgmTimeoutId = setTimeout(() => { if(state.soundOn) scheduleLoop(); else bgmPlaying=false; }, loopDur * 1000 - 100);
  }
  scheduleLoop();
}

function stopBGM() {
  bgmPlaying = false;
  clearTimeout(bgmTimeoutId);
}

function toggleSound() {
  state.soundOn = !state.soundOn;
  const btn = document.getElementById('soundBtn');
  btn.textContent = state.soundOn ? '🔊' : '🔇';
  btn.classList.toggle('muted', !state.soundOn);
  if (state.soundOn) playBGM();
  else stopBGM();
  showToast(state.soundOn ? '🔊 音效已开启' : '🔇 音效已关闭');
}

// 音效：收集金币
function playCoinSfx() {
  if (!state.soundOn) return;
  ensureAudio();
  [[988,0.08],[1319,0.12],[1568,0.1]].forEach(([f,d],i)=>{
    const o=audioCtx.createOscillator(), g=audioCtx.createGain();
    o.connect(g);g.connect(audioCtx.destination);
    o.type='square';o.frequency.value=f;
    const t=audioCtx.currentTime+i*0.07;
    g.gain.setValueAtTime(0.1,t);g.gain.exponentialRampToValueAtTime(0.001,t+d);
    o.start(t);o.stop(t+d+0.01);
  });
}

// 音效：跳跃
function playJumpSfx() {
  if (!state.soundOn) return;
  ensureAudio();
  const o=audioCtx.createOscillator(),g=audioCtx.createGain();
  o.connect(g);g.connect(audioCtx.destination);
  o.type='square';
  const t=audioCtx.currentTime;
  o.frequency.setValueAtTime(400,t);
  o.frequency.exponentialRampToValueAtTime(900,t+0.12);
  g.gain.setValueAtTime(0.08,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.15);
  o.start(t);o.stop(t+0.15);
}

// 音效：通关
function playLevelupSfx() {
  if (!state.soundOn) return;
  ensureAudio();
  const notes=[[523,0.1],[659,0.1],[784,0.1],[1047,0.25]];
  let t=audioCtx.currentTime;
  notes.forEach(([f,d])=>{
    const o=audioCtx.createOscillator(),g=audioCtx.createGain();
    o.connect(g);g.connect(audioCtx.destination);
    o.type='triangle';o.frequency.value=f;
    g.gain.setValueAtTime(0.1,t);g.gain.exponentialRampToValueAtTime(0.001,t+d);
    o.start(t);o.stop(t+d);t+=d;
  });
}

// 音效：蘑菇
function playMushroomSfx() {
  if (!state.soundOn) return;
  ensureAudio();
  [[330,0.08],[440,0.08],[550,0.08],[660,0.12]].forEach(([f,d],i)=>{
    const o=audioCtx.createOscillator(),g=audioCtx.createGain();
    o.connect(g);g.connect(audioCtx.destination);
    o.type='sawtooth';o.frequency.value=f;
    const t=audioCtx.currentTime+i*0.06;
    g.gain.setValueAtTime(0.07,t);g.gain.exponentialRampToValueAtTime(0.001,t+d);
    o.start(t);o.stop(t+d);
  });
}

// ============================================================
//  ===== 玩家控制 =====
// ============================================================
let isJumping = false;
let playerX = 40;
let autoMoveTimer = null;

function playerJump() {
  if (isJumping) return;
  isJumping = true;
  playJumpSfx();
  const p = document.getElementById('player');
  p.classList.add('jumping');
  p.classList.remove('running');
  setTimeout(() => {
    p.classList.remove('jumping');
    isJumping = false;
  }, 560);
}

function movePlayer(x) {
  playerX = Math.max(20, Math.min(window.innerWidth - 60, x));
  document.getElementById('player').style.left = playerX + 'px';
}

// 点击屏幕任意位置让角色跑过去
document.addEventListener('click', function(e) {
  if (e.target.closest('.app-container') || e.target.closest('.checkin-modal')) return;
  const p = document.getElementById('player');
  const targetX = e.clientX - 22;
  p.classList.add('running');
  const dir = targetX > playerX ? 1 : -1;
  p.style.transform = dir < 0 ? 'scaleX(-1)' : '';
  movePlayer(targetX);
  setTimeout(() => p.classList.remove('running'), 400);
});

// 键盘控制
document.addEventListener('keydown', e => {
  if (e.code === 'Space' || e.code === 'ArrowUp') { e.preventDefault(); playerJump(); }
  if (e.code === 'ArrowLeft') movePlayer(playerX - 30);
  if (e.code === 'ArrowRight') movePlayer(playerX + 30);
});

// ============================================================
//  ===== 问号砖块 =====
// ============================================================
function hitQBlock(el, id) {
  if (el.classList.contains('hit')) return;
  el.classList.add('hit');
  el.textContent = '📦';
  // 弹出金币
  const rect = el.getBoundingClientRect();
  spawnPopCoin(rect.left + 10, rect.top - 10);
  addCoins(3, el);
  playCoinSfx();
  // 随机5%几率出蘑菇
  if (Math.random() < 0.3) {
    setTimeout(() => spawnExtraMushroom(rect.left, rect.top), 500);
  }
}

function spawnPopCoin(x, y) {
  const el = document.createElement('div');
  el.className = 'pop-coin';
  el.style.cssText = `position:fixed;left:${x}px;top:${y}px;font-size:24px;pointer-events:none;z-index:200;`;
  el.textContent = '🪙';
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 700);
}

function spawnExtraMushroom(x, y) {
  const el = document.createElement('div');
  el.className = 'bg-mushroom';
  el.style.cssText = `position:fixed;left:${x}px;top:${y}px;font-size:28px;z-index:15;cursor:pointer;animation:coin-float 2s ease-in-out infinite;`;
  el.textContent = '🍄';
  el.onclick = () => collectMushroom(el);
  document.body.appendChild(el);
  setTimeout(() => { if(document.body.contains(el)) el.remove(); }, 8000);
}

// ============================================================
//  ===== 收集道具 =====
// ============================================================
function collectBgCoin(el) {
  playCoinSfx();
  const rect = el.getBoundingClientRect();
  addCoins(state.powerup ? 2 : 1, el);
  flyToNav(rect.left, rect.top);
  // 销毁后重生
  el.style.visibility = 'hidden';
  setTimeout(() => {
    el.style.visibility = '';
    el.style.animation = 'coin-float ease-in-out infinite';
    el.style.animationDelay = Math.random()*2 + 's';
    el.style.animationDuration = (2.5+Math.random()) + 's';
  }, 4000);
}

function collectMushroom(el) {
  playMushroomSfx();
  el.style.animation = 'mushroom-collect 0.4s ease forwards';
  // 激活加倍
  state.powerup = true;
  const banner = document.getElementById('powerupBanner');
  banner.classList.add('show');
  setTimeout(() => { banner.classList.remove('show'); }, 2200);
  setTimeout(() => { state.powerup = false; el.remove(); }, 400);
  addCoins(5, el);
  showToast('🍄 超级蘑菇！接下来金币×2！', 2500);
}

function flyToNav(fromX, fromY) {
  const el = document.createElement('div');
  el.className = 'fly-coin';
  const navCoin = document.querySelector('.coin-counter');
  const rect2 = navCoin.getBoundingClientRect();
  const tx = rect2.left - fromX + 16;
  const ty = rect2.top - fromY + 10;
  el.style.cssText = `left:${fromX}px;top:${fromY}px;--tx:${tx}px;--ty:${ty}px;`;
  el.textContent = '🪙';
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 850);
}

// ============================================================
//  ===== 金币系统 =====
// ============================================================
function addCoins(n, srcEl) {
  const add = state.powerup ? n * 2 : n;
  state.coins += add;
  document.getElementById('coinScore').textContent = state.coins;
  updateCoinGrid();
  // 弹出文字
  const popup = document.createElement('div');
  popup.style.cssText = `position:fixed;top:45%;left:50%;transform:translate(-50%,-50%);font-size:22px;
    font-weight:900;color:#ffd700;text-shadow:2px 2px 0 rgba(0,0,0,0.4);pointer-events:none;z-index:998;
    animation:coinPop 0.75s ease forwards;`;
  popup.textContent = `+${add}🪙`;
  document.body.appendChild(popup);
  setTimeout(() => popup.remove(), 780);
}

// 添加全局金币弹出动画
(function(){
  const s=document.createElement('style');
  s.textContent='@keyframes coinPop{0%{opacity:1;transform:translate(-50%,-50%) scale(0.5);}50%{opacity:1;transform:translate(-50%,-80%) scale(1.3);}100%{opacity:0;transform:translate(-50%,-120%) scale(1);}}';
  document.head.appendChild(s);
})();

function updateCoinGrid() {
  const grid = document.getElementById('coinGrid');
  const total = Math.min(state.coins, 20);
  grid.innerHTML = '';
  for (let i = 0; i < 20; i++) {
    const slot = document.createElement('div');
    slot.className = 'coin-slot' + (i < total ? ' earned' : '');
    slot.textContent = i < total ? '🪙' : '○';
    grid.appendChild(slot);
  }
}

function addAchievement(icon, title) {
  state.achievements.unshift({ icon, title, time: new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'}) });
  refreshAchLog();
}

function refreshAchLog() {
  const log = document.getElementById('achLog');
  if (!state.achievements.length) {
    log.innerHTML = '<div style="color:rgba(255,255,255,0.4);font-size:12px;text-align:center;padding:8px;">完成路标打卡可获得金币 ✨</div>';
    return;
  }
  log.innerHTML = state.achievements.slice(0,8).map(a=>
    `<div class="ach-item"><span class="ai">${a.icon}</span><span>${a.title}</span><span style="margin-left:auto;opacity:0.5;font-size:10px;">${a.time}</span></div>`
  ).join('');
}

// ============================================================
//  ===== 主题切换 =====
// ============================================================
function setTheme(cls, dot) {
  document.body.className = cls;
  document.querySelectorAll('.theme-dot').forEach(d => d.classList.remove('active'));
  dot.classList.add('active');
  showToast('✨ 主题已切换！');
  playCoinSfx();
}

// ============================================================
//  ===== 步骤导航 =====
// ============================================================
const stepProgress = [5,25,52,76,100];

function goToStep(n) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('screen-' + n).classList.add('active');
  document.getElementById('progressFill').style.width = stepProgress[n] + '%';
  document.getElementById('progressText').textContent = `第 ${n+1}/5 步`;
  document.querySelectorAll('.step-dot').forEach((d,i)=>{
    d.classList.remove('active','completed');
    if(i<n) d.classList.add('completed');
    if(i===n) d.classList.add('active');
  });
  state.step = n;
  if (n===2 && !Object.keys(state.mbti.answers).length) initMBTI();
  window.scrollTo({top:0,behavior:'smooth'});
  // 更新玩家角色
  document.getElementById('player').textContent = state.avatar;
  document.getElementById('rmRunner').textContent = state.avatar;
  // 返回按钮：首页隐藏，其他页面显示
  const backBtn = document.getElementById('navBackBtn');
  if (n > 0) { backBtn.classList.add('visible'); } else { backBtn.classList.remove('visible'); }
}

// 返回上一步
function goPrevStep() {
  if (state.step > 0) goToStep(state.step - 1);
}

// 复制API链接到剪贴板
function copyApiLink() {
  const url = 'https://platform.deepseek.com/api_keys';
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(()=>{
      const el = document.getElementById('apiLinkCopied');
      el.style.display = 'inline';
      showToast('📋 链接已复制！去浏览器粘贴打开');
      setTimeout(()=>{ el.style.display = 'none'; }, 5000);
    }).catch(()=> fallbackCopy(url));
  } else {
    fallbackCopy(url);
  }
}
function fallbackCopy(text) {
  const ta = document.createElement('textarea');
  ta.value = text; ta.style.position = 'fixed'; ta.style.left = '-9999px';
  document.body.appendChild(ta); ta.select();
  try { document.execCommand('copy');
    document.getElementById('apiLinkCopied').style.display = 'inline';
    showToast('📋 链接已复制！');
    setTimeout(()=>{ document.getElementById('apiLinkCopied').style.display = 'none'; }, 5000);
  } catch(e) { showToast('复制失败，请手动复制：' + text); }
  document.body.removeChild(ta);
}

// ============================================================
//  ===== 角色选择 =====
// ============================================================
function selectAvatar(el) {
  document.querySelectorAll('.avatar-opt').forEach(a=>a.classList.remove('selected'));
  el.classList.add('selected');
  state.avatar = el.dataset.char;
  document.getElementById('heroCharDisplay').textContent = state.avatar;
  document.getElementById('player').textContent = state.avatar;
  addCoins(1, el);
  playCoinSfx();
}

// ============================================================
//  ===== 标签选择 =====
// ============================================================
function toggleTag(el, group, single=false) {
  const val = el.dataset.val;
  if (single) {
    const siblings = el.closest('.tag-grid, .card').querySelectorAll('.tag-item');
    siblings.forEach(t=>t.classList.remove('selected'));
    state.sel[group] = [val];
    el.classList.add('selected');
  } else {
    const idx = state.sel[group].indexOf(val);
    if (idx===-1) { state.sel[group].push(val); el.classList.add('selected'); addCoins(1, el); playCoinSfx(); }
    else { state.sel[group].splice(idx,1); el.classList.remove('selected'); }
  }
}

function switchCityGroup(btn, group) {
  document.querySelectorAll('.city-tab').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll('.city-group').forEach(g=>g.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('city-'+group).classList.add('active');
}

// ============================================================
//  ===== Step1 验证 =====
// ============================================================
function validateAndGoStep2() {
  if (!state.sel.industry.length) {
    showToast('⚠️ 请至少选择一个行业方向！');
    document.getElementById('industryTags').classList.add('shake');
    setTimeout(()=>document.getElementById('industryTags').classList.remove('shake'),500);
    return;
  }
  if (!state.sel.city.length) { showToast('🗺️ 别忘了选择期望就业城市！'); return; }
  addCoins(10, document.getElementById('industryTags'));
  playLevelupSfx();
  showToast('🎉 目标已设定！获得金币+10');
  goToStep(2);
}

// ============================================================
//  ===== MBTI =====
// ============================================================
const mbtiQs = [
  {text:"在派对上，你更倾向于...",optA:"😄 主动认识新朋友",optB:"🤫 和老朋友聊",dim:"EI",aDir:"E"},
  {text:"面对新项目，你首先会...",optA:"📊 分析现有数据",optB:"💭 构思创新方案",dim:"SN",aDir:"S"},
  {text:"做决策时，更看重...",optA:"⚖️ 逻辑和客观事实",optB:"❤️ 别人感受和和谐",dim:"TF",aDir:"T"},
  {text:"你更喜欢的生活方式...",optA:"📅 有计划有安排",optB:"🎲 随机应变灵活",dim:"JP",aDir:"J"},
  {text:"独处时，你通常会...",optA:"⚡ 想着出去社交",optB:"🔋 享受独处充电",dim:"EI",aDir:"E"},
  {text:"你更信任什么信息？",optA:"🔍 亲眼所见可查事实",optB:"✨ 直觉感知整体印象",dim:"SN",aDir:"S"},
  {text:"批评他人时，你更可能...",optA:"🎯 直接指出问题",optB:"🌸 委婉先肯定再建议",dim:"TF",aDir:"T"},
  {text:"出行旅游，你更喜欢...",optA:"🗺️ 提前规划好",optB:"🧳 随性说走就走",dim:"JP",aDir:"J"},
  {text:"团队中，你倾向...",optA:"🙋 积极主导讨论",optB:"🎧 深思熟虑后发言",dim:"EI",aDir:"E"},
  {text:"解决复杂问题，你喜欢...",optA:"🔧 运用已有经验",optB:"🌀 探索新方法打破常规",dim:"SN",aDir:"S"},
  {text:"朋友倾诉烦恼，你倾向...",optA:"🧩 分析提方案",optB:"🫂 先给予情感支持",dim:"TF",aDir:"T"},
  {text:"面对截止日期，你通常...",optA:"⏰ 提前完成不喜欢压力",optB:"🔥 最后冲刺效率更高",dim:"JP",aDir:"J"},
];

const mbtiData = {
  "INTJ":{name:"建筑师",char:"🦉",color:"#6633cc",desc:"独立、有远见、战略性思维极强。追求效率和完美，能洞察他人看不到的可能性。",careers:["战略分析师","产品经理","科学家","工程师","投资顾问","程序员"]},
  "INTP":{name:"逻辑学家",char:"🔭",color:"#3366ff",desc:"逻辑严密、好奇心旺盛。热爱探索复杂理论，总能找到问题的本质。",careers:["研究员","数据科学家","软件开发","学者","系统分析师","哲学家"]},
  "ENTJ":{name:"指挥官",char:"🦁",color:"#cc2200",desc:"天生领导者，自信、果断、目标导向。善于制定长期计划，推动变革。",careers:["CEO","项目总监","律师","金融分析师","创业者","咨询顾问"]},
  "ENTP":{name:"辩论家",char:"🦊",color:"#ff6600",desc:"机智、创新、充满活力。喜欢挑战现状，天生的创意家。",careers:["创业者","律师","顾问","市场总监","产品创新","编剧"]},
  "INFJ":{name:"提倡者",char:"🦋",color:"#9933cc",desc:"富有洞察力、理想主义。深刻理解他人，致力于让世界变得更好。",careers:["心理咨询师","作家","教育者","社工","HR","公益人士"]},
  "INFP":{name:"调停者",char:"🌸",color:"#ff66aa",desc:"理想主义、有创造力，忠于自己的价值观。富有艺术感。",careers:["作家","设计师","心理咨询师","教育者","艺术家","UX设计"]},
  "ENFJ":{name:"主人公",char:"🌟",color:"#ff9900",desc:"有感召力、善于激励他人。能理解并引导他人，是优秀的沟通者。",careers:["教师","培训师","HR总监","政治家","公关","团队领导"]},
  "ENFP":{name:"活动家",char:"🌈",color:"#ff6699",desc:"热情、有创造力、善于联结。对未来充满期待，点子层出不穷。",careers:["市场营销","创意总监","演讲者","记者","公关","创业者"]},
  "ISTJ":{name:"物流师",char:"🏛️",color:"#446699",desc:"可靠、有条理、踏实负责。注重细节，履行承诺，最可信赖的人。",careers:["会计","审计师","项目经理","公务员","律师","银行家"]},
  "ISFJ":{name:"守护者",char:"🛡️",color:"#336699",desc:"温暖、细心、有责任感。默默付出，关注他人需求。",careers:["护士","教师","行政管理","HR","社工","客服经理"]},
  "ESTJ":{name:"总经理",char:"👔",color:"#cc4400",desc:"务实、果断、注重秩序。善于管理流程和团队。",careers:["管理者","项目经理","法官","政府官员","金融顾问","军官"]},
  "ESFJ":{name:"执政官",char:"🤗",color:"#ff4488",desc:"热情、有爱心、关注他人。总是把他人的需求放在首位。",careers:["教师","护士","人力资源","销售","活动策划","客户经理"]},
  "ISTP":{name:"鉴赏家",char:"🔧",color:"#448844",desc:"灵活、擅长实践、独立。天生的工匠，善于找到实用解决方案。",careers:["工程师","飞行员","程序员","外科医生","机械师","侦探"]},
  "ISFP":{name:"探险家",char:"🎨",color:"#cc8800",desc:"温柔、有艺术感。有独特审美，喜欢用创造力表达自己。",careers:["设计师","摄影师","厨师","艺术家","兽医","时尚设计"]},
  "ESTP":{name:"企业家",char:"🏄",color:"#cc3300",desc:"大胆、聪明、感知力强。充满活力，善于把握当下机遇。",careers:["销售总监","创业者","演员","谈判专家","经纪人","消防员"]},
  "ESFP":{name:"表演者",char:"🎭",color:"#ff3399",desc:"自发、热情、活力四射。让生活充满乐趣，天生的表演者。",careers:["演员","活动策划","销售","幼儿教育","DJ","主播"]},
};

let mbtiScores = {E:0,I:0,S:0,N:0,T:0,F:0,J:0,P:0};

function initMBTI() {
  state.mbti.q = 0;
  mbtiScores = {E:0,I:0,S:0,N:0,T:0,F:0,J:0,P:0};
  renderMBTIQ(0);
  document.getElementById('mbti-result-area').style.display='none';
  document.getElementById('mbti-quiz-area').style.display='block';
}

function restartMBTI() { state.mbti.answers={}; initMBTI(); }

function renderMBTIQ(idx) {
  if(idx>=mbtiQs.length){finishMBTI();return;}
  const q=mbtiQs[idx];
  document.getElementById('mbti-quiz-area').innerHTML=`
    <div class="question-card">
      <div class="q-num">❓ 第${idx+1}/${mbtiQs.length}题
        <div style="margin-left:auto;background:#f0f0f0;border-radius:6px;height:6px;width:110px;overflow:hidden;">
          <div style="height:100%;background:linear-gradient(90deg,var(--primary),var(--secondary));width:${((idx+1)/mbtiQs.length)*100}%;border-radius:6px;transition:width 0.4s;"></div>
        </div>
      </div>
      <div class="q-text">${q.text}</div>
      <div class="answer-options">
        <button class="answer-btn" onclick="answerMBTI('A','${q.dim}',${idx},this)">${q.optA}</button>
        <button class="answer-btn" onclick="answerMBTI('B','${q.dim}',${idx},this)">${q.optB}</button>
      </div>
    </div>
    <div style="text-align:center;color:rgba(255,255,255,0.65);font-size:11px;margin-top:6px;">请选择最符合你真实状态的选项 🎯</div>`;
}

function answerMBTI(choice, dim, idx, btn) {
  btn.classList.add(choice==='A'?'sel-a':'sel-b');
  btn.parentElement.querySelectorAll('.answer-btn').forEach(b=>b.onclick=null);
  const dims=dim.split('');
  mbtiScores[choice==='A'?dims[0]:dims[1]]++;
  state.mbti.answers[idx]=choice;
  addCoins(2, btn);
  playCoinSfx();
  setTimeout(()=>renderMBTIQ(idx+1),480);
}

function finishMBTI() {
  const type=[mbtiScores.E>=mbtiScores.I?'E':'I',mbtiScores.S>=mbtiScores.N?'S':'N',
    mbtiScores.T>=mbtiScores.F?'T':'F',mbtiScores.J>=mbtiScores.P?'J':'P'].join('');
  state.mbti.result=type;
  const d=mbtiData[type]||mbtiData['ENFP'];
  document.getElementById('mbti-quiz-area').style.display='none';
  document.getElementById('mbti-result-area').style.display='block';
  document.getElementById('mbtiTypeDisplay').textContent=type;
  document.getElementById('mbtiTypeDisplay').style.color=d.color;
  document.getElementById('mbtiTypeName').textContent=`「${d.name}」`;
  document.getElementById('mbtiChar').textContent=d.char;
  document.getElementById('mbtiDescription').innerHTML=`<div style="font-weight:800;color:#333;margin-bottom:5px;">${d.char} ${d.name}</div><div style="font-size:12px;color:#555;line-height:1.6;">${d.desc}</div>`;
  const colors=['#ff6633','#3366ff','#00aa44','#9933cc','#ff9900','#cc2200'];
  document.getElementById('careerBadges').innerHTML=d.careers.map((c,i)=>`
    <div class="career-badge fade-in" style="background:${colors[i%6]}20;color:${colors[i%6]};border:2px solid ${colors[i%6]}44;animation-delay:${i*0.08}s;">${c}</div>`).join('');
  addCoins(20, document.getElementById('mbtiTypeDisplay'));
  playLevelupSfx();
  addAchievement('🧠', `MBTI测评完成：${type} ${d.name}`);
  showToast(`🎉 你是 ${type} ${d.name}！获得金币+20`);
}

// ============================================================
//  ===== 经历增删 =====
// ============================================================
function addInternship(){
  const l=document.getElementById('internshipList'),d=document.createElement('div');
  d.className='exp-item fade-in';
  d.innerHTML=`<div class="exp-header"><input class="form-input exp-title-input" style="margin:0;font-weight:700;" placeholder="公司名称" type="text"><button class="exp-remove" onclick="removeExp(this)">×</button></div>
    <input class="form-input" style="margin-top:6px;" placeholder="岗位名称" type="text">
    <div style="display:flex;gap:7px;margin-top:6px;"><input class="form-input" style="flex:1;" placeholder="开始时间" type="month"><input class="form-input" style="flex:1;" placeholder="结束时间" type="month"></div>
    <input class="form-input" style="margin-top:6px;" placeholder="主要工作内容" type="text">`;
  l.appendChild(d);
}
function addCompetition(){
  const l=document.getElementById('competitionList'),d=document.createElement('div');
  d.className='exp-item fade-in';
  d.innerHTML=`<div class="exp-header"><input class="form-input exp-title-input" style="margin:0;font-weight:700;" placeholder="竞赛名称" type="text"><button class="exp-remove" onclick="removeExp(this)">×</button></div>
    <div style="display:flex;gap:7px;margin-top:6px;"><input class="form-input" style="flex:1;" placeholder="获奖等级" type="text"><input class="form-input" style="flex:1;" placeholder="年份" type="text"></div>`;
  l.appendChild(d);
}
function addPublication(){
  const l=document.getElementById('publicationList'),d=document.createElement('div');
  d.className='exp-item fade-in';
  d.innerHTML=`<div class="exp-header"><input class="form-input exp-title-input" style="margin:0;" placeholder="论文/专利名称" type="text"><button class="exp-remove" onclick="removeExp(this)">×</button></div>
    <div style="display:flex;gap:7px;margin-top:6px;"><select class="form-select" style="flex:1;"><option value="">成果类型</option><option>期刊论文</option><option>会议论文</option><option>专利</option></select><input class="form-input" style="flex:1;" placeholder="年份" type="text"></div>`;
  l.appendChild(d);
}
function removeExp(btn){
  const i=btn.closest('.exp-item');
  i.style.cssText='transform:scale(0.85);opacity:0;transition:all 0.3s;';
  setTimeout(()=>i.remove(),300);
}

// ============================================================
//  ===== 保存 & 恢复简历表单数据 =====
// ============================================================
function saveFormData() {
  state.form = {
    age: document.getElementById('userAge').value,
    major: document.getElementById('userMajor').value,
    degree: document.getElementById('userDegree').value,
    grade: document.getElementById('userGrade').value,
    school: document.getElementById('userSchool').value,
    schoolLevel: document.getElementById('userSchoolLevel').value,
    gradYear: document.getElementById('userGradYear').value,
    gpa: document.getElementById('userGPA').value,
    other: document.getElementById('otherAchieve').value,
    apiKey: document.getElementById('apiKeyInput').value,
    apiBaseUrl: document.getElementById('apiBaseUrl').value,
    apiModel: document.getElementById('apiModel').value,
  };
}
function restoreFormData() {
  const f = state.form;
  if (!f) return;
  if (f.age) document.getElementById('userAge').value = f.age;
  if (f.major) document.getElementById('userMajor').value = f.major;
  if (f.degree) document.getElementById('userDegree').value = f.degree;
  if (f.grade) document.getElementById('userGrade').value = f.grade;
  if (f.school) document.getElementById('userSchool').value = f.school;
  if (f.schoolLevel) document.getElementById('userSchoolLevel').value = f.schoolLevel;
  if (f.gradYear) document.getElementById('userGradYear').value = f.gradYear;
  if (f.gpa) document.getElementById('userGPA').value = f.gpa;
  if (f.other) document.getElementById('otherAchieve').value = f.other;
  if (f.apiKey) document.getElementById('apiKeyInput').value = f.apiKey;
  if (f.apiBaseUrl) document.getElementById('apiBaseUrl').value = f.apiBaseUrl;
  if (f.apiModel) document.getElementById('apiModel').value = f.apiModel;
}
// 恢复标签选择状态
function restoreTagSelections() {
  const groups = ['industry','job','company','city','goal','eng','skill'];
  groups.forEach(g => {
    const vals = state.sel[g];
    document.querySelectorAll(`[onclick*="'${g}'"]`).forEach(el => {
      if (vals.includes(el.dataset.val)) el.classList.add('selected');
    });
  });
}

// ============================================================
//  ===== 重新规划 =====
// ============================================================
function replanKeepData() {
  saveFormData();
  goToStep(1);
  setTimeout(() => {
    restoreFormData();
    restoreTagSelections();
    showToast('✏️ 已保留你的信息，可修改后重新生成');
  }, 300);
}
function replanFresh() {
  // 重置选择和表单，但保留金币和成就
  state.sel = { industry:[], job:[], company:[], city:[], goal:[], eng:[], skill:[] };
  state.mbti = { answers:{}, result:null, q:0 };
  state.form = {};
  state.checkedNodes = {};
  document.querySelectorAll('.tag-item.selected').forEach(el=>el.classList.remove('selected'));
  ['userAge','userMajor','userGPA','userSchool','otherAchieve'].forEach(id=>{
    const el=document.getElementById(id); if(el) el.value='';
  });
  ['userDegree','userGrade','userGradYear'].forEach(id=>{
    const el=document.getElementById(id); if(el) el.value='';
  });
  goToStep(0);
  showToast('🔄 已重置，开始新的冒险！');
}

// ============================================================
//  ===== AI 驱动的规划生成（DeepSeek API） =====
// ============================================================

// 标签值到中文名的映射
const labelMap = {
  industry:{finance:'金融',internet:'互联网',ai:'人工智能',robot:'机器人',material:'材料科学',
    biotech:'生物医药',energy:'新能源',auto:'新能源汽车',edu:'教育培训',gov:'政府机构',
    consult:'咨询管理',chip:'芯片半导体',space:'航空航天',media:'新媒体'},
  job:{rd:'研发/技术',product:'产品设计',ops:'运营',sales:'市场/销售',finance_pos:'财务/会计',
    research:'科研/学术',data:'数据分析',manage:'项目管理'},
  company:{bigtech:'互联网大厂',soe:'国有企业',private:'民营企业',startup:'初创公司',
    civil:'公务员',public:'事业单位',foreign:'外资企业',research_inst:'科研院所',
    academia:'高校教职',freelance:'自由职业'},
  city:{beijing:'北京',shanghai:'上海',guangzhou:'广州',shenzhen:'深圳',hangzhou:'杭州',
    chengdu:'成都',wuhan:'武汉',nanjing:'南京',xian:'西安',chongqing:'重庆',hefei:'合肥',
    other_city:'其他城市',us:'美国',europe:'欧洲',singapore:'新加坡',hk:'香港'},
  goal:{firstjob:'找到理想工作',phd:'深造读博',abroad_study:'出国留学',startup_goal:'自主创业',
    public_goal:'考公考编',promote:'晋升管理层'},
  eng:{cet4:'CET-4',cet6:'CET-6',ielts:'雅思',toefl:'托福',native:'母语水平'},
  skill:{python:'Python',java:'Java',cpp:'C/C++',ml:'机器学习',finance_skill:'金融建模',
    design:'UI设计',lab:'实验室技能'}
};
const levelMap = {bachelor:'本科',master:'硕士',phd:'博士'};
const schoolLevelMap = {985:'985高校',211:'211高校',double_first:'双一流高校',regular:'普通本科',
  junior_college:'专科/高职院校',overseas_top:'海外名校(QS前100)',overseas:'海外普通高校'};

// 收集实习/竞赛/学术数据
function collectExperienceData() {
  const internships=[], competitions=[], publications=[];
  document.querySelectorAll('#internshipList .exp-item').forEach(item=>{
    const inputs = item.querySelectorAll('input');
    internships.push({
      company: inputs[0]?.value||'', role: inputs[1]?.value||'',
      start: inputs[2]?.value||'', end: inputs[3]?.value||'', desc: inputs[4]?.value||''
    });
  });
  document.querySelectorAll('#competitionList .exp-item').forEach(item=>{
    const inputs = item.querySelectorAll('input');
    competitions.push({name: inputs[0]?.value||'', award: inputs[1]?.value||'', year: inputs[2]?.value||''});
  });
  document.querySelectorAll('#publicationList .exp-item').forEach(item=>{
    const inputs = item.querySelectorAll('input');
    publications.push({title: inputs[0]?.value||'', type: item.querySelector('select')?.value||'', year: inputs[1]?.value||''});
  });
  return {internships, competitions, publications};
}

// 测试 API Key
async function testApiKey() {
  const key = document.getElementById('apiKeyInput').value.trim();
  const base = document.getElementById('apiBaseUrl').value.trim() || 'https://api.deepseek.com';
  const model = document.getElementById('apiModel').value.trim() || 'deepseek-chat';
  if (!key) { showToast('⚠️ 请先输入 API Key'); return; }
  try {
  const base2 = base.replace(/\/+$/, '');
  const apiBase = base2.endsWith('/v1') ? base2 : base2 + '/v1';
  const resp = await fetch(`${apiBase}/chat/completions`, {
    method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+key},
    body:JSON.stringify({model, messages:[{role:'user',content:'Hi'}], max_tokens:5})
  });
    if (resp.ok) { showToast('✅ API Key 有效，连接成功！'); }
    else { const e=await resp.json(); showToast('❌ '+((e.error&&e.error.message)||'连接失败')); }
  } catch(e) { showToast('❌ 网络错误：'+e.message); }
}

// 调用 AI API
async function askDeepSeek(systemPrompt, userMessage) {
  const key = document.getElementById('apiKeyInput').value.trim();
  const base = document.getElementById('apiBaseUrl').value.trim() || 'https://api.deepseek.com';
  const model = document.getElementById('apiModel').value.trim() || 'deepseek-chat';
  const base2 = base.replace(/\/+$/, '');
  const apiBase = base2.endsWith('/v1') ? base2 : base2 + '/v1';
  const resp = await fetch(`${apiBase}/chat/completions`, {
    method:'POST',
    headers:{'Content-Type':'application/json','Authorization':'Bearer '+key},
    body:JSON.stringify({
      model,
      messages:[
        {role:'system',content:systemPrompt},
        {role:'user',content:userMessage}
      ],
      temperature:0.7,
      max_tokens:3000,
      response_format:{type:'json_object'}
    })
  });
  if (!resp.ok) {
    const err = await resp.json().catch(()=>({}));
    throw new Error(err.error?.message || `API 返回 ${resp.status}`);
  }
  const data = await resp.json();
  const text = data.choices?.[0]?.message?.content || '';
  // 提取JSON（可能被```json包裹）
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error('AI 返回了非 JSON 格式的内容');
  return JSON.parse(jsonMatch[0]);
}

// 构建 AI Prompt
function buildAIPrompt() {
  const {industry,job,company,city,goal,eng,skill} = state.sel;
  const f = state.form;
  const mbtiType = state.mbti.result || '未知';
  const expData = collectExperienceData();

  const indNames = industry.map(v=>labelMap.industry[v]||v);
  const jobNames = job.map(v=>labelMap.job[v]||v);
  const compNames = company.map(v=>labelMap.company[v]||v);
  const cityNames = city.map(v=>labelMap.city[v]||v);
  const goalNames = goal.map(v=>labelMap.goal[v]||v);
  const engNames = eng.map(v=>labelMap.eng[v]||v);
  const skillNames = skill.map(v=>labelMap.skill[v]||v);
  const degreeName = levelMap[f.degree]||f.degree||'未填写';
  const schoolLv = schoolLevelMap[f.schoolLevel]||'未填写';

  const userInfo = `年龄:${f.age||'未填写'} | 专业:${f.major||'未填写'} | 学历:${degreeName} | 年级:${glabel(f.grade)} | 学校:${f.school||'未填写'}(${schoolLv}) | 预计毕业:${f.gradYear||'未知'}年 | GPA:${f.gpa||'未填写'}`;
  const prefInfo = `意向行业:${indNames.join('、')||'未选择'} | 岗位类型:${jobNames.join('、')||'未选择'} | 公司类型:${compNames.join('、')||'未选择'} | 期望城市:${cityNames.join('、')||'未选择'} | 五年目标:${goalNames.join('、')||'未选择'} | 英语:${engNames.join('、')||'无'} | 技能:${skillNames.join('、')||'无'} | MBTI:${mbtiType}`;

  let expInfo = '';
  if (expData.internships.length) expInfo += '\n实习经历:\n'+expData.internships.map((e,i)=>`${i+1}. ${e.company} ${e.role} (${e.start}~${e.end}) ${e.desc}`).join('\n');
  if (expData.competitions.length) expInfo += '\n竞赛经历:\n'+expData.competitions.map((e,i)=>`${i+1}. ${e.name} ${e.award} (${e.year})`).join('\n');
  if (expData.publications.length) expInfo += '\n学术成果:\n'+expData.publications.map((e,i)=>`${i+1}. ${e.title} (${e.type}, ${e.year})`).join('\n');
  if (f.other) expInfo += '\n其他:'+f.other;

  const systemPrompt = `你是一位资深的职画，擅长为大学生制定个性化的职业发展方案。请根据用户的基本信息、发展意向和经历，给出专业、具体、可操作的职业规划建议。

你必须返回纯JSON格式，包含以下字段：
{
  "advices": [
    {"icon":"emoji图标","title":"简短标题(6-10字)","text":"详细建议文本(80-150字)，要具体可操作"}
  ],
  "companies": [
    {"name":"公司名称","logo":"一个最能代表该公司的emoji","desc":"该公司简介和推荐理由(30-50字)","tag":"推荐标签(如:大厂实习/央企秋招/投行暑期)"}
  ],
  "milestones": [
    {"id":"n0","icon":"emoji","color":"#hex颜色","label":"简短标题(4-6字)","time":"时间范围","desc":"该阶段具体任务描述(30-50字)","checkinType":"text或internship或competition","checkinLabel":"打卡提示文字","done":false}
  ]
}

要求：
1. advices 提供3-5条个性化建议，必须结合用户的MBTI类型、学历档次、行业方向来写，不能泛泛而谈
2. companies 推荐3-5家具体公司，必须真实存在，包含大厂、行业龙头、新锐公司，针对用户意向行业和岗位
3. milestones 提供从当前阶段到毕业的6-9个里程碑节点，每个节点要具体到做什么、什么时间做
4. milestones 的 id 从 n0 开始递增，checkinType 根据内容选择合适类型（text=纯文字记录,internship=实习记录,competition=竞赛记录）
5. 所有建议必须考虑用户当前年级和毕业时间，倒推安排时间线
6. 如果用户学历档次较高(985/211/海外名校)，可以建议更有野心的目标；如果是普通本科，建议务实的路径`;

  const userMessage = `请为我制定职业规划。\n\n【基本信息】${userInfo}\n【发展意向】${prefInfo}\n${expInfo?'【已有经历】'+expInfo:'【已有经历】暂无'}`;

  return {systemPrompt, userMessage};
}

// 重写 generatePlan：优先AI生成，失败时fallback到本地
async function generatePlan() {
  saveFormData();
  const {industry,company} = state.sel;
  const grade = document.getElementById('userGrade').value;
  const gradYear = document.getElementById('userGradYear').value;
  const mbtiType = state.mbti.result || 'ENFP';
  const apiKey = document.getElementById('apiKeyInput').value.trim();

  // 更新总结区域
  const imap={finance:'💰',internet:'🌐',ai:'🤖',robot:'🦾',material:'🔬',chip:'💻',space:'🚀',energy:'⚡'};
  const fi = industry[0]||'';
  const fname = {finance:'金融',internet:'互联网',ai:'人工智能',robot:'机器人',material:'材料',chip:'芯片',space:'航天',energy:'新能源',biotech:'生物医药',auto:'新能源汽车'}[fi]||'目标行业';
  document.getElementById('summaryEmoji').textContent = imap[fi]||'🎮';
  document.getElementById('summaryTitle').textContent = `向${fname}出发！`;
  document.getElementById('summaryDesc').textContent = `基于 MBTI ${mbtiType} + ${fname}方向，量身定制从${glabel(grade)}到毕业的闯关路线 🎮`;

  // 立即跳转到结果页，展示加载动画 + 小游戏
  const adviceList = document.getElementById('adviceList');
  const aiLoading = document.getElementById('aiLoadingArea');
  const aiError = document.getElementById('aiErrorArea');
  adviceList.innerHTML = '';
  aiLoading.style.display = 'block';
  aiError.style.display = 'none';
  goToStep(4);

  // 启动小恐龙游戏
  setTimeout(()=> startDinoGame(), 300);

  if (apiKey) {
    try {
      const {systemPrompt, userMessage} = buildAIPrompt();
      const result = await askDeepSeek(systemPrompt, userMessage);

      // 停止小游戏，隐藏加载动画
      stopDinoGame();
      aiLoading.style.display = 'none';

      // 渲染AI建议
      let html = '';
      if (result.advices && result.advices.length) {
        html += result.advices.map((a,i)=>
          `<div class="ai-suggestion-card fade-in" style="animation-delay:${i*0.1}s;">
            <div class="sug-title">${a.icon||'💡'} ${a.title||'建议'}</div>
            <div class="sug-text">${a.text||''}</div>
          </div>`).join('');
      }
      // 渲染推荐公司
      if (result.companies && result.companies.length) {
        html += `<div class="ai-suggestion-card fade-in" style="animation-delay:${(result.advices?.length||0)*0.1}s;">
          <div class="sug-title">🏢 推荐目标公司</div>
          <div class="ai-company-list">${result.companies.map(c=>
            `<div class="ai-company-item">
              <span class="ci-logo">${c.logo||'🏢'}</span>
              <div class="ci-info">
                <div class="ci-name">${c.name||''}</div>
                <div class="ci-desc">${c.desc||''}</div>
              </div>
              ${c.tag?`<span class="ci-tag">${c.tag}</span>`:''}
            </div>`).join('')}
          </div>
        </div>`;
      }
      adviceList.innerHTML = html;

      // 用AI返回的milestones渲染路线图
      if (result.milestones && result.milestones.length) {
        state.milestones = result.milestones.map(m=>({
          id: m.id||('n'+Math.random().toString(36).substr(2,4)),
          icon: m.icon||'📍', color: m.color||'#6366f1',
          label: m.label||'里程碑', time: m.time||'待定',
          desc: m.desc||'', checkinType: m.checkinType||'text',
          checkinLabel: m.checkinLabel||'记录你的经历', done: !!m.done
        }));
      } else {
        state.milestones = genMilestones(grade, gradYear, industry, company);
      }

      renderHRoadmap();
      addCoins(50, document.getElementById('summaryCard'));
      playLevelupSfx();
      addAchievement('🤖','AI 生成专属职业规划');
      showToast('🤖 AI 规划生成成功！');
      return;
    } catch(e) {
      console.warn('AI generation failed, fallback:', e);
      stopDinoGame();
      aiLoading.style.display = 'none';
      aiError.innerHTML = `<div class="ai-error">🤖 AI 生成失败：${e.message}<br>已自动切换为本地智能规划模式，你可以检查 API Key 后重试。</div>`;
      aiError.style.display = 'block';
    }
  }

  // Fallback：本地生成（也要停止游戏）
  stopDinoGame();
  aiLoading.style.display = 'none';
  const advices = genAdvices(industry, company, mbtiType, grade);
  adviceList.innerHTML = advices.map((a,i)=>
    `<div class="advice-item fade-in" style="animation-delay:${i*0.08}s;">
      <div class="advice-icon">${a.icon}</div>
      <div class="advice-content"><strong>${a.title}</strong><p>${a.text}</p></div>
    </div>`).join('');

  state.milestones = genMilestones(grade, gradYear, industry, company);
  renderHRoadmap();
  addCoins(50, document.getElementById('summaryCard'));
  playLevelupSfx();
  addAchievement('🗺️','生成专属职业规划路线图');
  showToast('🎉 路线图生成！获得金币+50！',3000);
}



function glabel(g) {
  return {freshman:'大一',sophomore:'大二',junior:'大三',senior:'大四',
    master1:'研一',master2:'研二',master3:'研三',
    phd1:'博一',phd2:'博二',phd3:'博三',phd4:'博四',phd5:'博五',graduated:'毕业后'}[g]||'当前';
}

function genAdvices(industry,company,mbti,grade) {
  const d=mbtiData[mbti]||mbtiData['ENFP'],advs=[];
  advs.push({icon:'🎯',title:`发挥 ${mbti} 型优势`,text:d.desc+'建议在求职中重点突出这些特质，选择能充分施展天赋的岗位。'});
  if(industry.includes('ai')||industry.includes('internet')||industry.includes('chip'))
    advs.push({icon:'💻',title:'技术能力建设',text:'深入学习Python/机器学习，参与GitHub开源项目，刷LeetCode算法题，大二/研一前完成核心技能栈。'});
  if(industry.includes('finance'))
    advs.push({icon:'💹',title:'金融行业敲门砖',text:'备考CFA/CPA，刷各大投行笔试题，争取大三/研一暑期拿到知名金融机构实习offer。'});
  if(company.includes('bigtech')||company.includes('startup'))
    advs.push({icon:'🏢',title:'大厂策略',text:'提前准备算法面试、产品案例、行为面试题。实习经历极其重要，尽早联系内部员工内推。'});
  if(company.includes('soe')||company.includes('civil')||company.includes('public'))
    advs.push({icon:'🏛️',title:'体制内求职路线',text:'国考通常11月笔试，提前半年系统备考行测+申论。同时关注央企校园招聘秋招项目。'});
  advs.push({icon:'🌟',title:'简历亮点打造',text:'大厂实习>行业知名竞赛>校园重要职务。每段经历用STAR法则量化成果：情景→任务→行动→结果。'});
  return advs;
}

function genMilestones(grade,gradYear,industry,company) {
  const now=new Date().getFullYear();
  const grYears={freshman:4,sophomore:3,junior:2,senior:1,master1:3,master2:2,master3:1,phd1:5,phd2:4,phd3:3,phd4:2,phd5:1,graduated:0};
  const left=grYears[grade]!==undefined?grYears[grade]:2;
  const gYear=parseInt(gradYear)||now+left;
  const isGov=company.includes('civil')||company.includes('soe')||company.includes('public');
  const isTech=industry.includes('ai')||industry.includes('internet')||industry.includes('chip');
  const isFin=industry.includes('finance');
  const nodes=[];
  nodes.push({id:'n0',icon:'🎮',color:'#6633cc',label:'开启冒险',time:'📍 现在',desc:'明确方向，开始有针对性地积累经验',checkinType:'text',checkinLabel:'写下你的起航宣言',done:false});
  if(left>=3) nodes.push({id:'n1',icon:'📚',color:'#3366ff',label:'打好基础',time:`${now+1}年`,desc:isTech?'刷算法、做项目、参加技术社团':isFin?'学金融建模，备考CFA L1':'扎实专业，参与科研项目',checkinType:'text',checkinLabel:'记录你的学习计划',done:false});
  if(left>=2){
    nodes.push({id:'n2',icon:'🏆',color:'#ff9900',label:'参加竞赛',time:`${now+Math.max(1,left-2)}年`,desc:isTech?'互联网+、ACM、挑战杯':isFin?'CFA大赛、证券投资大赛':'挑战杯、创青春、互联网+',checkinType:'competition',checkinLabel:'记录你参加的竞赛',done:false});
    nodes.push({id:'n3',icon:'💼',color:'#00aa44',label:'第一次实习',time:`${now+Math.max(1,left-2)}年暑期`,desc:isGov?'国企/政府机关实习':isTech?'中小型互联网公司实习':'行业相关公司积累经验',checkinType:'internship',checkinLabel:'记录这段实习经历',done:false});
  }
  if(left>=1){
    nodes.push({id:'n4',icon:'🌟',color:'#ff6633',label:'目标公司实习',time:`${gYear-1}年暑期`,desc:isGov?'参加央企/国企秋招':isTech?'冲击BAT/字节/华为大厂暑期实习':isFin?'冲击顶级投行/基金实习':'进入心仪公司实习，争取转正',checkinType:'internship',checkinLabel:'记录你的大厂/目标公司实习',done:false});
  }
  nodes.push({id:'n5',icon:'📋',color:'#9933cc',label:'秋招黄金季',time:`${gYear-1}年9-10月`,desc:'更新简历、准备面试、广投简历。秋招是最重要的求职窗口！',checkinType:'text',checkinLabel:'记录你的秋招准备情况',done:false});
  if(!isGov) nodes.push({id:'n6',icon:'📝',color:'#cc4400',label:'笔试面试冲刺',time:`${gYear-1}年10-11月`,desc:'每天刷2道题，做3个模拟面试，准备网申笔试、技术/专业面试',checkinType:'text',checkinLabel:'记录你的面试经历',done:false});
  else nodes.push({id:'n6',icon:'📝',color:'#cc4400',label:'国考/省考笔试',time:`${gYear-1}年11月`,desc:'提前6个月备考行测+申论，参加国考和目标省份省考',checkinType:'text',checkinLabel:'记录你的备考心得',done:false});
  nodes.push({id:'n7',icon:'🎯',color:'#ff3366',label:'春招补录',time:`${gYear}年3-5月`,desc:'秋招未果可参加春招，持续优化简历，积极争取内推机会',checkinType:'text',checkinLabel:'春招进展记录',done:false});
  nodes.push({id:'n8',icon:'🎓',color:'#ffd700',label:'毕业！',time:`${gYear}年6-7月`,desc:'带着积累的技能、人脉和经验，自信出发，开始新征程！',checkinType:'text',checkinLabel:'写下你的毕业感言',done:false});
  return nodes;
}

// ============================================================
//  ===== 横向马里奥路线图 渲染 =====
// ============================================================
function renderHRoadmap() {
  const track = document.getElementById('roadmapTrackH');
  const nodeColors = state.milestones.map(m=>m.color);
  let html = '<div class="rm-ground"></div>';
  // 跑步角色
  html += `<div class="rm-runner" id="rmRunner" style="left:30px;">${state.avatar}</div>`;

  state.milestones.forEach((m, i) => {
    const isDone = !!state.checkedNodes[m.id];
    const nodeStyle = isDone
      ? `background:linear-gradient(135deg,#ffd700,#ff9900);`
      : `background:linear-gradient(135deg,${m.color},${m.color}99);`;
    html += `
      <div class="rm-node ${isDone?'done':''}" id="rn-${m.id}" data-idx="${i}" onclick="clickNode(${i})">
        <div class="rm-node-inner" style="${nodeStyle}" title="${m.label}">
          ${isDone?'🪙':m.icon}
          ${isDone?`<span class="rm-flag">🚩</span>`:''}
        </div>
        <div class="rm-node-label">${m.label}</div>
        <div class="rm-node-time">${m.time}</div>
      </div>
    `;
    if (i < state.milestones.length - 1) {
      html += `<div class="rm-connector ${isDone?'done-conn':''}"></div>`;
    }
  });
  track.innerHTML = html;

  // 把小人移到第一个已完成节点之后
  const completedCount = state.milestones.filter(m=>state.checkedNodes[m.id]).length;
  setTimeout(() => moveRunnerTo(completedCount), 300);
}

function moveRunnerTo(nodeIdx) {
  const runner = document.getElementById('rmRunner');
  if (!runner) return;
  // 估算每个节点宽约120px（90节点+30连接），加上起始偏移
  const x = 20 + nodeIdx * 120 + (nodeIdx>0?10:0);
  runner.style.left = x + 'px';
  runner.classList.add('moving');
  setTimeout(()=>runner.classList.remove('moving'), 500);
}

// ============================================================
//  ===== 路标打卡 =====
// ============================================================
let currentNodeIdx = -1;

function clickNode(idx) {
  const m = state.milestones[idx];
  if (!m) return;
  currentNodeIdx = idx;
  const isDone = !!state.checkedNodes[m.id];
  // 打开弹窗
  document.getElementById('ciIcon').textContent = isDone ? '✅' : m.icon;
  document.getElementById('ciTitle').textContent = isDone ? `已完成：${m.label}` : `打卡：${m.label}`;
  document.getElementById('ciSubtitle').textContent = isDone ? '可以修改你的记录' : `${m.time} · ${m.desc}`;

  const existing = state.checkedNodes[m.id] || {};
  let bodyHtml = '';
  if (m.checkinType === 'internship') {
    bodyHtml = `
      <div class="form-group"><div class="form-label">🏢 公司名称</div>
        <input class="form-input" id="ci_company" placeholder="公司名称" value="${existing.company||''}"></div>
      <div class="form-group"><div class="form-label">💼 岗位名称</div>
        <input class="form-input" id="ci_role" placeholder="如：产品实习生" value="${existing.role||''}"></div>
      <div class="form-group"><div class="form-label">📝 主要工作</div>
        <textarea class="form-input" id="ci_note" rows="2" style="resize:none;" placeholder="简要描述你做了什么...">${existing.note||''}</textarea></div>
    `;
  } else if (m.checkinType === 'competition') {
    bodyHtml = `
      <div class="form-group"><div class="form-label">🏆 竞赛名称</div>
        <input class="form-input" id="ci_compname" placeholder="竞赛名称" value="${existing.compname||''}"></div>
      <div class="form-group"><div class="form-label">🥇 获奖情况</div>
        <input class="form-input" id="ci_award" placeholder="如：国家级二等奖" value="${existing.award||''}"></div>
      <div class="form-group"><div class="form-label">💬 感想</div>
        <textarea class="form-input" id="ci_note" rows="2" style="resize:none;" placeholder="参赛感想...">${existing.note||''}</textarea></div>
    `;
  } else {
    bodyHtml = `
      <div class="form-group"><div class="form-label">✍️ ${m.checkinLabel}</div>
        <textarea class="form-input" id="ci_note" rows="3" style="resize:none;" placeholder="写下你的经历或感想...">${existing.note||''}</textarea></div>
    `;
  }
  document.getElementById('ciBody').innerHTML = bodyHtml;
  document.getElementById('checkinModal').classList.add('open');
  playJumpSfx();
}

function closeCheckin() {
  document.getElementById('checkinModal').classList.remove('open');
  currentNodeIdx = -1;
}

function confirmCheckin() {
  if (currentNodeIdx < 0) return;
  const m = state.milestones[currentNodeIdx];
  const noteEl = document.getElementById('ci_note');
  const note = noteEl ? noteEl.value.trim() : '';
  if (!note) { showToast('✍️ 请先写下你的经历哦！'); noteEl && noteEl.focus(); return; }

  // 收集额外字段
  const extra = {};
  ['ci_company','ci_role','ci_compname','ci_award'].forEach(id=>{
    const el=document.getElementById(id); if(el) extra[id.replace('ci_','')]=el.value;
  });
  const wasNew = !state.checkedNodes[m.id];
  state.checkedNodes[m.id] = { note, ...extra, time: new Date().toLocaleString('zh-CN') };
  m.done = true;
  closeCheckin();

  if (wasNew) {
    addCoins(state.powerup ? 20 : 10, document.getElementById('rn-'+m.id));
    playCoinSfx();
    addAchievement(m.icon, `路标打卡：${m.label}`);
    showToast(`🪙 打卡成功！${m.label} +10金币！`, 2500);
    // 同步简历
    syncCheckinToResume(m, extra, note);
  } else {
    showToast('✅ 记录已更新！');
  }
  // 重新渲染路线图
  renderHRoadmap();
  // 小人移动到当前节点
  moveRunnerTo(currentNodeIdx + 1);
}

// 将打卡内容同步到简历信息
function syncCheckinToResume(m, extra, note) {
  if (m.checkinType === 'internship' && extra.company) {
    const list = document.getElementById('internshipList');
    const div = document.createElement('div');
    div.className = 'exp-item fade-in';
    div.innerHTML = `<div class="exp-header">
      <input class="form-input exp-title-input" style="margin:0;font-weight:700;" value="${extra.company||''}" type="text">
      <button class="exp-remove" onclick="removeExp(this)">×</button>
    </div>
    <input class="form-input" style="margin-top:6px;" value="${extra.role||''}" placeholder="岗位名称" type="text">
    <input class="form-input" style="margin-top:6px;" value="${note}" placeholder="主要工作内容" type="text">`;
    list.appendChild(div);
  } else if (m.checkinType === 'competition' && extra.compname) {
    const list = document.getElementById('competitionList');
    const div = document.createElement('div');
    div.className = 'exp-item fade-in';
    div.innerHTML = `<div class="exp-header">
      <input class="form-input exp-title-input" style="margin:0;font-weight:700;" value="${extra.compname||''}" type="text">
      <button class="exp-remove" onclick="removeExp(this)">×</button>
    </div>
    <div style="display:flex;gap:7px;margin-top:6px;">
      <input class="form-input" style="flex:1;" value="${extra.award||''}" placeholder="获奖等级" type="text">
    </div>`;
    list.appendChild(div);
  }
}

// ============================================================
//  ===== 吐司 =====
// ============================================================
function showToast(msg, dur=2200) {
  const t=document.getElementById('toastMsg');
  t.textContent=msg;t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),dur);
}

// ============================================================
//  ===== 初始化 =====
// ============================================================
// ============================================================
//  ===== 小恐龙闯关游戏 (等待时消遣) =====
// ============================================================
let dinoGame = {
  running: false, over: false, score: 0, animId: null,
  dino: null, obstacles: [], frame: 0, speed: 3, W: 0, H: 0, ctx: null, canvas: null
};

function dinoDrawGround() {
  const g = dinoGame;
  g.ctx.fillStyle = '#ddd';
  g.ctx.fillRect(0, g.H-12, g.W, 3);
}

function dinoDrawDino() {
  const g = dinoGame, d = g.dino;
  g.ctx.fillStyle = '#555';
  g.ctx.fillRect(d.x, d.y, d.w, d.h);
  g.ctx.fillStyle = '#444';
  g.ctx.fillRect(d.x+18, d.y-10, 16, 18);
  g.ctx.fillStyle = 'white';
  g.ctx.fillRect(d.x+28, d.y-6, 4, 4);
  const legOff = (g.frame % 20 < 10) ? 3 : -3;
  g.ctx.fillStyle = '#444';
  g.ctx.fillRect(d.x+4, d.y+d.h, 6, 10+legOff);
  g.ctx.fillRect(d.x+18, d.y+d.h, 6, 10-legOff);
}

function dinoDrawObstacle(ob) {
  const g = dinoGame;
  g.ctx.fillStyle = '#2d7d3a';
  g.ctx.fillRect(ob.x, ob.y, ob.w, ob.h);
  g.ctx.fillRect(ob.x-5, ob.y+5, 6, 12);
  g.ctx.fillRect(ob.x+ob.w-1, ob.y+8, 6, 10);
}

function dinoJump() {
  const d = dinoGame.dino;
  if (d.onGround) { d.vy = -13; d.onGround = false; }
}

function dinoLoop() {
  const g = dinoGame;
  if (!g.running) return;
  g.ctx.clearRect(0, 0, g.W, g.H);
  dinoDrawGround();

  // 重力
  g.dino.vy += 0.7;
  g.dino.y += g.dino.vy;
  if (g.dino.y >= g.H-40) { g.dino.y = g.H-40; g.dino.vy = 0; g.dino.onGround = true; }
  dinoDrawDino();

  // 生成障碍物
  if (g.frame % Math.max(80, 120-g.speed*5) === 0) {
    g.obstacles.push({ x: g.W+10, y: g.H-55, w: 14, h: 36 });
  }

  // 更新障碍物 + 碰撞检测
  g.obstacles = g.obstacles.filter(ob => {
    ob.x -= g.speed;
    dinoDrawObstacle(ob);
    const d = g.dino;
    if (ob.x < d.x+d.w && ob.x+ob.w > d.x && ob.y < d.y+d.h && ob.y+ob.h > d.y) {
      g.over = true;
      g.running = false;
      g.ctx.fillStyle = 'rgba(0,0,0,0.5)';
      g.ctx.fillRect(0, 0, g.W, g.H);
      g.ctx.fillStyle = 'white';
      g.ctx.font = 'bold 18px sans-serif';
      g.ctx.textAlign = 'center';
      g.ctx.fillText('游戏结束！', g.W/2, g.H/2-10);
      g.ctx.font = '13px sans-serif';
      g.ctx.fillText('点击或按空格重来', g.W/2, g.H/2+15);
      return false;
    }
    return ob.x > -30;
  });

  // 分数
  if (!g.over) {
    g.score = Math.floor(g.frame / 6);
    g.speed = Math.min(8, 3 + g.score / 200);
  }
  g.ctx.fillStyle = '#888';
  g.ctx.font = '12px monospace';
  g.ctx.textAlign = 'right';
  g.ctx.fillText('🏆 ' + g.score, g.W-10, 20);

  // 云朵
  g.ctx.fillStyle = 'rgba(0,0,0,0.05)';
  const cx = ((g.frame * 0.5) % (g.W+40)) - 20;
  g.ctx.beginPath();
  g.ctx.arc(cx, 25, 10, 0, Math.PI*2);
  g.ctx.arc(cx+12, 22, 13, 0, Math.PI*2);
  g.ctx.arc(cx+24, 25, 10, 0, Math.PI*2);
  g.ctx.fill();

  g.frame++;
  if (!g.over) g.animId = requestAnimationFrame(dinoLoop);
  const scoreEl = document.getElementById('dinoScore');
  if (scoreEl) scoreEl.textContent = '分数: ' + g.score;
}

function startDinoGame() {
  const canvas = document.getElementById('dinoGame');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;

  dinoGame = {
    running: true, over: false, score: 0, animId: null,
    dino: { x:40, y:H-40, w:28, h:36, vy:0, onGround:true },
    obstacles: [], frame: 0, speed: 3, W, H, ctx, canvas
  };

  if (dinoGame.animId) cancelAnimationFrame(dinoGame.animId);

  // 事件监听
  dinoGame._jh = (e) => {
    if (e.type === 'keydown' && e.code !== 'Space') return;
    e.preventDefault();
    if (dinoGame.over) { startDinoGame(); return; }
    dinoJump();
  };
  document.removeEventListener('keydown', dinoGame._jhOld);
  canvas.removeEventListener('click', dinoGame._jhOld);
  dinoGame._jhOld = dinoGame._jh;
  document.addEventListener('keydown', dinoGame._jh);
  canvas.addEventListener('click', dinoGame._jh);

  dinoLoop();
}

function stopDinoGame() {
  dinoGame.running = false;
  if (dinoGame.animId) cancelAnimationFrame(dinoGame.animId);
  document.removeEventListener('keydown', dinoGame._jhOld);
  if (dinoGame.canvas) dinoGame.canvas.removeEventListener('click', dinoGame._jhOld);
}

// ============================================================
window.addEventListener('load', () => {
  // 初始化金币格子
  updateCoinGrid();
  // 自动启动BGM（需要用户交互触发）
  document.addEventListener('click', function startBGM() {
    if (state.soundOn) playBGM();
    document.removeEventListener('click', startBGM);
  }, { once: true });
  // 设置玩家角色
  document.getElementById('player').textContent = state.avatar;
});
