'use strict';
const $=id=>document.getElementById(id);
const path=location.pathname;
document.querySelectorAll('nav a').forEach(a=>{if(a.getAttribute('href')===path)a.setAttribute('aria-current','page');});
if(path==='/') initArt(); else initExperience();

function initArt(){
  const canvas=$('network'),ctx=canvas.getContext('2d'),reduce=matchMedia('(prefers-reduced-motion: reduce)');
  // Decorative illustration only, never presented as inference.
  const skeleton=[[.5,.15],[.5,.24],[.38,.29],[.62,.29],[.27,.18],[.73,.18],[.2,.07],[.8,.07],[.43,.51],[.57,.51],[.35,.71],[.65,.71],[.26,.91],[.74,.91]];
  const edges=[[0,1],[1,2],[1,3],[2,4],[4,6],[3,5],[5,7],[2,8],[3,9],[8,9],[8,10],[10,12],[9,11],[11,13]];
  let mouse=0,frame;
  canvas.addEventListener('pointermove',e=>{mouse=(e.offsetX/canvas.clientWidth-.5)*.04;});
  function draw(t=0){
    const r=canvas.getBoundingClientRect(),d=Math.min(devicePixelRatio,2);canvas.width=r.width*d;canvas.height=r.height*d;ctx.scale(d,d);ctx.clearRect(0,0,r.width,r.height);
    const pts=skeleton.map(([x,y],i)=>[(x+mouse+(!reduce.matches?Math.sin(t/1600+i)*.006:0))*r.width,y*r.height*.85+35]);
    for(let i=0;i<95;i++){
      const a=edges[i%edges.length],f=(i*.618)%1,p=pts[a[0]],q=pts[a[1]],x=p[0]+(q[0]-p[0])*f+Math.sin(i*7)*24,y=p[1]+(q[1]-p[1])*f+Math.cos(i*9)*20;
      ctx.strokeStyle='#2ab4d32a';ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(p[0],p[1]);ctx.stroke();ctx.fillStyle='#57dfec99';ctx.fillRect(x,y,2,2);
    }
    ctx.lineWidth=1.5;ctx.strokeStyle='#52e7ed9c';for(const [a,b]of edges){ctx.beginPath();ctx.moveTo(...pts[a]);ctx.lineTo(...pts[b]);ctx.stroke();}
    pts.forEach((p,i)=>{ctx.fillStyle='#68f6ff';ctx.shadowBlur=15;ctx.shadowColor='#52e7ed';ctx.beginPath();ctx.arc(...p,i===0?12:4,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;ctx.strokeStyle='#52e7ed44';ctx.strokeRect(p[0]-10,p[1]-10,20,20);});
    if(!reduce.matches&&!document.hidden)frame=requestAnimationFrame(draw);
  }
  document.addEventListener('visibilitychange',()=>{cancelAnimationFrame(frame);if(!document.hidden)draw();});
  reduce.addEventListener('change',()=>{cancelAnimationFrame(frame);draw();});window.addEventListener('resize',()=>{if(reduce.matches)draw();});draw();
}

function initExperience(){
  const hand=path==='/numeros',video=$('video'),out=$('output'),ctx=out.getContext('2d'),capture=document.createElement('canvas'),c=capture.getContext('2d');
  $('home').hidden=true;$('experience').hidden=false;
  $('lab-label').textContent=hand?'EXPERIMENTO 02 / MÃO':'EXPERIMENTO 01 / CORPO';
  $('experience-title').textContent=hand?'O número está na sua mão.':'Movimente. Conte. Descubra.';
  $('instructions').textContent=hand?'Mostre uma mão aberta para a câmera. Levante de zero a cinco dedos. Isto é uma contagem de dedos, não reconhecimento de Libras.':'Fique de frente, com o corpo inteiro visível. Comece com braços para baixo e pés juntos. Abra braços acima da cabeça e pernas; depois feche.';
  $('tips-text').textContent=hand?'Mantenha a palma voltada para a câmera, os dedos separados e a mão inteira visível. Segure o gesto por um instante. Evite mostrar a mão de lado.':'Afaste-se até que cabeça, mãos levantadas e pés caibam na imagem. A contagem exige fechar → abrir → fechar. Use um espaço seguro para se movimentar.';
  $('result-label').textContent=hand?'DEDOS LEVANTADOS':'REPETIÇÕES COMPLETAS';$('goal').hidden=hand;$('demo').hidden=hand;$('reset').hidden=hand;$('pause').hidden=hand;
  let ws=null,stream=null,active=false,ready=false,paused=false,pending=null,timer=null,watchdog=null,epoch=0,id=0,demo=false,resetting=false,lastResult=null,control='reset';
  function status(text){$('status').textContent=text;}
  function buttons(){ $('start').disabled=active;$('demo').disabled=active;$('stop').disabled=!active;$('pause').disabled=!ready;$('reset').disabled=!ready; }
  function stop(message='Experiência encerrada. Câmera desligada.'){
    epoch++;active=false;ready=false;paused=false;pending=null;resetting=false;lastResult=null;
    clearTimeout(timer);clearTimeout(watchdog);
    if(ws){ws.onclose=null;ws.onmessage=null;ws.close();ws=null;}
    if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}
    video.pause();video.srcObject=null;video.removeAttribute('src');video.load();
    ctx.clearRect(0,0,out.width,out.height);$('camera-placeholder').hidden=false;$('source-label').textContent='CÂMERA / DESLIGADA';$('value').textContent='—';$('progress').value=0;$('workspace')?.classList.remove('complete');document.querySelector('.workspace').classList.remove('complete');$('pause').textContent='Pausar';buttons();status(message);
  }
  async function start(useDemo){
    stop('Preparando detector…');active=true;demo=useDemo;buttons();const token=epoch;
    try{
      if(!useDemo){
        if(!navigator.mediaDevices?.getUserMedia)throw new Error('A câmera exige localhost ou uma conexão HTTPS.');
        const s=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480}},audio:false});
        if(token!==epoch){s.getTracks().forEach(t=>t.stop());return;}stream=s;video.srcObject=s;
        s.getVideoTracks()[0].addEventListener('ended',()=>{if(active)stop('A câmera foi desconectada. Conecte-a e inicie novamente.');});
      }else{video.src='/demo.mp4';video.loop=false;}
      await video.play();if(token!==epoch)return;
      if(useDemo)video.pause(); // Do not consume the beginning while the model loads.
      $('source-label').textContent=demo?'DEMONSTRAÇÃO / VÍDEO GRAVADO':'CÂMERA / AO VIVO';
      ws=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/${hand?'hand':'pose'}`);
      watchdog=setTimeout(()=>stop('Tempo de conexão esgotado. Confira se o servidor está ativo.'),20000);
      ws.onmessage=e=>{
        if(token!==epoch)return;
        const data=JSON.parse(e.data);clearTimeout(watchdog);
        if(data.type==='error'){stop(data.message);return;}
        if(data.type==='ready'){ready=true;buttons();status('Detector pronto. Posicione-se.');video.play().then(send).catch(()=>stop('Não foi possível iniciar o vídeo.'));}
        if(data.type==='reset'){resetting=false;$('value').textContent=data.value;$('progress').value=data.value;document.querySelector('.workspace').classList.toggle('complete',data.value>=5);status('Pronto. Comece na posição fechada.');schedule();}
        if(data.type==='result'&&pending===data.id){
          pending=null;
          if(!paused&&!resetting){lastResult=data;draw(data);$('value').textContent=data.value??'—';$('progress').value=data.value??0;const complete=!hand&&data.value>=5;document.querySelector('.workspace').classList.toggle('complete',complete);status(complete?'Meta concluída! Você completou 5 repetições.':data.status);}
          if(resetting)ws.send(JSON.stringify({type:control}));else schedule();
        }
      };
      ws.onclose=()=>{if(active)stop('Conexão perdida. Verifique o servidor e inicie novamente.');};
      ws.onerror=()=>{if(active)stop('Não foi possível conectar ao Python. Verifique o servidor.');};
    }catch(err){if(token!==epoch)return;const messages={NotAllowedError:'Permissão de câmera negada. Permita o acesso nas configurações do navegador.',NotFoundError:'Nenhuma câmera encontrada. Conecte uma webcam ou use o vídeo gravado.',NotReadableError:'Câmera indisponível. Feche outros aplicativos que estejam usando a webcam.'};stop(messages[err.name]||err.message||'Não foi possível iniciar a câmera.');}
  }
  function schedule(){clearTimeout(timer);if(active&&!paused&&!resetting)timer=setTimeout(send,85);}
  function send(){
    if(!active||paused||resetting||pending!==null||ws?.readyState!==WebSocket.OPEN)return;
    if(!video.videoWidth){schedule();return;}
    const scale=Math.min(640/video.videoWidth,480/video.videoHeight,1);capture.width=Math.max(1,Math.round(video.videoWidth*scale));capture.height=Math.max(1,Math.round(video.videoHeight*scale));
    c.drawImage(video,0,0,capture.width,capture.height);pending=++id;
    ws.send(JSON.stringify({id:pending,image:capture.toDataURL('image/jpeg',.85).split(',')[1]}));
    watchdog=setTimeout(()=>stop('O processamento demorou demais. Inicie novamente.'),15000);
  }
  function draw(data){
    out.width=capture.width;out.height=capture.height;ctx.drawImage(capture,0,0);$('camera-placeholder').hidden=true;
    if(!$('points').checked)return;
    ctx.lineWidth=2;ctx.strokeStyle='#52e7ed';const p=data.points;
    for(const [a,b]of data.edges){if(!p[a]||!p[b]||(p[a][3]??1)<.45||(p[b][3]??1)<.45)continue;ctx.beginPath();ctx.moveTo(p[a][0]*out.width,p[a][1]*out.height);ctx.lineTo(p[b][0]*out.width,p[b][1]*out.height);ctx.stroke();}
    p.forEach((v,i)=>{if((v[3]??1)<.45)return;const finger=[4,8,12,16,20].indexOf(i);ctx.fillStyle=hand&&finger>=0?(data.raised[finger]?'#b4ff72':'#ffaf7b'):'#edffff';ctx.beginPath();ctx.arc(v[0]*out.width,v[1]*out.height,3.5,0,Math.PI*2);ctx.fill();});
  }
  $('start').onclick=()=>start(false);$('demo').onclick=()=>start(true);$('stop').onclick=()=>stop();
  $('pause').onclick=()=>{paused=!paused;$('pause').textContent=paused?'Continuar':'Pausar';if(paused){video.pause();clearTimeout(timer);status('Pausado. A câmera permanece ligada.');}else{video.play().then(()=>{control='resume';resetting=true;status('Retomando a partir da posição fechada…');if(pending===null)ws.send(JSON.stringify({type:control}));}).catch(()=>stop('Não foi possível retomar o vídeo.'));}};
  $('reset').onclick=()=>{control='reset';resetting=true;clearTimeout(timer);status('Zerando contagem…');if(pending===null&&ws?.readyState===1)ws.send(JSON.stringify({type:control}));};
  $('points').onchange=()=>{if(lastResult&&pending===null)draw(lastResult);};
  video.onended=()=>{clearTimeout(timer);paused=true;$('pause').disabled=true;status('Fim do vídeo gravado. Encerre e inicie outra demonstração.');};
  video.onerror=()=>{if(active)stop('Não foi possível abrir o vídeo gravado. Confira app/assets/polichinelos.mp4.');};
  window.addEventListener('pagehide',()=>stop());document.addEventListener('visibilitychange',()=>{if(document.hidden&&active)stop('Experiência encerrada ao sair da aba. Inicie novamente para participar.');});
}
