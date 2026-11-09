import { chromium } from '../blood_flood/report_preview/node_modules/playwright-core/index.mjs';
import { writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const dir=path.resolve('outputs/CeilingWorker_2026-11-08/Revision18');
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1400,height:1000}});const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(dir,'Просмотр_сотрудника_v18.html')).href);
 const pictures=page.locator('figure img');if(await pictures.count()!==11)throw Error('Expected 11 pictures');
 for(const image of await pictures.all()){await image.scrollIntoViewIfNeeded();await image.evaluate(el=>el.decode());}
 await page.locator('[data-index="0"]').click();
 if(!await page.locator('dialog').evaluate(d=>d.open))throw Error('Viewer did not open');
 await page.locator('#next').click();if(!(await page.locator('#title').textContent()).startsWith('2 / 11'))throw Error('Next failed');
 await page.keyboard.press('ArrowLeft');if(!(await page.locator('#title').textContent()).startsWith('1 / 11'))throw Error('Arrow navigation failed');
 await page.keyboard.press('Escape');if(await page.locator('dialog').evaluate(d=>d.open))throw Error('Escape failed');
 const video=page.locator('video');await video.evaluate(v=>new Promise((resolve,reject)=>{if(v.readyState>=1)return resolve();v.addEventListener('loadedmetadata',resolve,{once:true});v.addEventListener('error',()=>reject(Error('Video could not load')),{once:true});v.load()}));
 const media=await video.evaluate(v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight}));
 if(Math.abs(media.duration-10)>.3)throw Error('Wrong example duration '+media.duration);
 await video.evaluate(async v=>{v.muted=true;v.currentTime=4;await v.play()});await page.waitForTimeout(450);await video.evaluate(v=>v.pause());
 const played=await video.evaluate(v=>v.currentTime);if(played<=4)throw Error('Video playback failed');
 for(const width of [1400,390]){await page.setViewportSize({width,height:1000});await page.evaluate(()=>scrollTo(0,0));if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('Horizontal overflow '+width);await page.screenshot({path:path.join(dir,'Review_'+width+'.png')});}
 if(errors.length)throw Error(errors.join('; '));
 const result={images:11,viewer:'open,next,keyboard previous,Escape',media,playbackAdvanced:played>4,responsive:[1400,390],scriptErrors:errors};
 await writeFile(path.join(dir,'Gallery_Check.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 // Inspect two actual decoded movie frames, not just the poster image.
 await page.setViewportSize({width:1100,height:900});await page.locator('video').scrollIntoViewIfNeeded();
 for(const seconds of [1,5.5,8]){await video.evaluate((v,t)=>new Promise(resolve=>{v.addEventListener('seeked',resolve,{once:true});v.currentTime=t}),seconds);await video.screenshot({path:path.join(dir,'Video_Frame_'+seconds+'.png')});}
}finally{await browser.close()}
