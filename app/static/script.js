// ── AUTH ──────────────────────────────────────────────
function fillDemo(){document.getElementById('email').value='admin@gassense.in';document.getElementById('password').value='gas1234'}
function doLogin(){
  const e=document.getElementById('email').value,p=document.getElementById('password').value;
  if(e==='admin@gassense.in'&&p==='gas1234'){
    document.getElementById('login-page').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    startLiveUpdates();
  }else{
    const a=document.getElementById('login-alert');a.style.display='block';
    setTimeout(()=>a.style.display='none',4000);
  }
}
function doLogout(){document.getElementById('app').classList.add('hidden');document.getElementById('login-page').classList.remove('hidden')}
document.getElementById('password').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin()});

// ── SIDEBAR DRAWER ────────────────────────────────────
function openSidebar(){
  document.getElementById('sidebar').classList.add('open');
  document.getElementById('sidebar-overlay').classList.add('show');
}
function closeSidebar(){
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebar-overlay').classList.remove('show');
}

// ── NAVIGATION ────────────────────────────────────────
function navTo(page,el){
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  if(el)el.classList.add('active');
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  const pg=document.getElementById('page-'+page);
  if(pg)pg.classList.add('active');
  const titles={dashboard:'Dashboard',live:'Live Monitor',alerts:'Alerts & Alarms',valve:'Valve Control',cylinder:'Cylinder Health',booking:'Gas Booking',analytics:'Analytics',history:'History Log',supply:'Supply Centre',settings:'Settings'};
  document.getElementById('page-title').textContent=titles[page]||page;
  closeSidebar();
}
function setBottomActive(el){
  document.querySelectorAll('.bnav-item').forEach(i=>i.classList.remove('active'));
  el.classList.add('active');
  // also sync sidebar nav
  const pageMap={0:'dashboard',1:'live',2:'alerts',3:'valve'};
  const idx=Array.from(document.querySelectorAll('.bnav-item')).indexOf(el);
  const navItems=document.querySelectorAll('.nav-item');
  navItems.forEach(n=>n.classList.remove('active'));
  const targetPage=pageMap[idx];
  if(targetPage){
    navItems.forEach(n=>{if(n.textContent.trim().toLowerCase().startsWith(targetPage.substring(0,4)))n.classList.add('active')});
  }
}

// ── LIVE DATA ─────────────────────────────────────────
let gasLevel=72,ppm=0,pressure=420,valveOpen=true,leakActive=false;
let liveData=Array(60).fill(0);

function startLiveUpdates(){
  setInterval(updateLive,2000);
  drawCanvas();
  setInterval(drawCanvas,2000);
}

function updateLive(){
  if(!leakActive){ppm=Math.max(0,ppm+(Math.random()-.7)*5);ppm=Math.min(ppm,30);}
  pressure=420+Math.round((Math.random()-.5)*20);
  gasLevel=Math.max(0,gasLevel-0.05);
  liveData.push(Math.round(ppm));
  if(liveData.length>60)liveData.shift();
  document.getElementById('live-ppm').textContent=Math.round(ppm);
  document.getElementById('live-ppm').style.color=ppm>500?'var(--red)':ppm>200?'var(--yellow)':'var(--green)';
  document.getElementById('live-level').textContent=Math.round(gasLevel);
  document.getElementById('live-pressure').textContent=pressure;
  document.getElementById('gauge-num').textContent=Math.round(gasLevel)+'%';
  document.getElementById('stat-level').textContent=Math.round(gasLevel)+'%';
  const angle=-90+(gasLevel/100)*180;
  const rad=angle*Math.PI/180;
  const nx=100+65*Math.cos(rad),ny=100+65*Math.sin(rad);
  document.getElementById('gauge-needle').setAttribute('x2',nx);
  document.getElementById('gauge-needle').setAttribute('y2',ny);
  const dash=251.2*(1-gasLevel/100);
  document.getElementById('gauge-fill').style.strokeDashoffset=dash;
  document.getElementById('level-indicator').style.left=Math.round(gasLevel)+'%';
  const lvlEl=document.getElementById('stat-level');
  lvlEl.style.color=gasLevel<15?'var(--red)':gasLevel<30?'var(--yellow)':'var(--green)';
}

function drawCanvas(){
  const canvas=document.getElementById('live-canvas');
  if(!canvas)return;
  const ctx=canvas.getContext('2d');
  const W=canvas.width,H=canvas.height;
  ctx.clearRect(0,0,W,H);
  ctx.strokeStyle='rgba(255,255,255,0.05)';ctx.lineWidth=1;
  for(let i=0;i<5;i++){const y=H/5*i;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
  ctx.fillStyle='rgba(148,163,184,0.6)';ctx.font='10px DM Sans';
  ctx.fillText('500',4,12);ctx.fillText('200',4,H*0.6);ctx.fillText('0',4,H-4);
  if(liveData.length<2)return;
  const step=W/(liveData.length-1);
  ctx.beginPath();
  liveData.forEach((v,i)=>{const x=i*step,y=H-(v/600)*H;i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);});
  ctx.strokeStyle=leakActive?'#ef4444':'#f97316';ctx.lineWidth=2;ctx.stroke();
  ctx.lineTo(W,H);ctx.lineTo(0,H);ctx.closePath();
  const grad=ctx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0,leakActive?'rgba(239,68,68,0.3)':'rgba(249,115,22,0.3)');
  grad.addColorStop(1,'rgba(249,115,22,0)');
  ctx.fillStyle=grad;ctx.fill();
}

// ── LEAK SIMULATION ───────────────────────────────────
function simulateLeak(){
  leakActive=true;ppm=530;
  const ring=document.getElementById('leak-ring');
  ring.className='leak-ring danger';ring.textContent='⚠️';
  document.getElementById('leak-ppm').textContent='530 PPM';
  document.getElementById('leak-badge').className='badge badge-red';
  document.getElementById('leak-badge').textContent='⚠ HIGH LEAK DETECTED!';
  document.getElementById('stat-leak-val').textContent='DANGER';
  document.getElementById('stat-leak-val').style.color='var(--red)';
  document.getElementById('stat-leak-sub').textContent='530 PPM — Critical!';
  document.getElementById('stat-alerts').textContent=4;
  document.getElementById('alert-count').textContent=4;
  document.getElementById('bnav-badge').textContent=4;
  document.getElementById('buzzer-wave').classList.remove('off');
  if(document.getElementById('buzzer-wave2'))document.getElementById('buzzer-wave2').classList.remove('off');
  setValve(false);
  showFloatAlert('High PPM (530)! Valve auto-closed. Buzzer activated. Supply centre notified.');
  setTimeout(()=>{
    leakActive=false;ppm=0;
    ring.className='leak-ring safe';ring.textContent='🛡️';
    document.getElementById('leak-ppm').textContent='0 PPM';
    document.getElementById('leak-badge').className='badge badge-green';
    document.getElementById('leak-badge').textContent='✓ No Leak Detected';
    document.getElementById('stat-leak-val').textContent='SAFE';
    document.getElementById('stat-leak-val').style.color='var(--green)';
    document.getElementById('stat-leak-sub').textContent='0 PPM detected';
    document.getElementById('buzzer-wave').classList.add('off');
    if(document.getElementById('buzzer-wave2'))document.getElementById('buzzer-wave2').classList.add('off');
  },8000);
}

function showFloatAlert(msg){
  document.getElementById('float-msg').textContent=msg;
  const a=document.getElementById('float-alert');
  a.classList.add('show');
  setTimeout(()=>a.classList.remove('show'),8000);
}

// ── VALVE ─────────────────────────────────────────────
function setValve(open){
  valveOpen=open;
  document.getElementById('valve-emoji').textContent=open?'🔓':'🔒';
  document.getElementById('valve-state-text').textContent='Valve '+(open?'OPEN':'CLOSED');
  document.getElementById('valve-desc').textContent=open?'Gas is flowing normally. Safe to use.':'Gas flow stopped. Open when area is safe.';
  document.getElementById('stat-valve').textContent=open?'OPEN':'CLOSED';
  document.getElementById('stat-valve').style.color=open?'var(--green)':'var(--red)';
  document.getElementById('btn-close-valve').style.opacity=open?'1':'0.4';
  document.getElementById('btn-close-valve').style.pointerEvents=open?'auto':'none';
  document.getElementById('btn-open-valve').style.opacity=open?'0.4':'1';
  document.getElementById('btn-open-valve').style.pointerEvents=open?'none':'auto';
  document.getElementById('valve-sensor-status').innerHTML=open?'<span class="dot dot-green"></span>Open':'<span class="dot dot-red"></span>Closed';
  if(!open&&!leakActive)showFloatAlert('Valve manually closed via remote control.');
}

// ── MISC ──────────────────────────────────────────────
function testBuzzer(){
  const bw=document.getElementById('buzzer-wave2');
  const st=document.getElementById('buzzer-status-text');
  bw.classList.remove('off');st.textContent='Buzzer: ACTIVE 🔔';
  setTimeout(()=>{bw.classList.add('off');st.textContent='Buzzer: Standby';},3000);
}
function clearAlerts(){
  document.querySelectorAll('.alert-list-item').forEach(i=>i.remove());
  document.getElementById('alert-count').textContent=0;
  document.getElementById('bnav-badge').textContent=0;
  document.getElementById('stat-alerts').textContent=0;
}
function sendSupplyAlert(){showFloatAlert('Emergency alert sent to Indane Gas Supply Centre!');}