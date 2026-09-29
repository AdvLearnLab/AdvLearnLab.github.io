---
layout: homepage
title: PDF 转可编辑 Word
permalink: /pdf-to-word.html
---

<script src="https://cdn.jsdelivr.net/npm/docx@8.5.0/build/index.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>

<div class="pdf-word-tool">
  <header class="pdf-word-hero">
    <span>Editable Document Conversion</span>
    <h1>PDF 转可编辑 Word</h1>
    <p>正文转换为可编辑段落；数学公式经专用模型识别为 LaTeX，并写入 Word 原生公式对象。</p>
  </header>
  <section class="pdf-word-local" aria-labelledby="pdf-word-local-title">
    <div><strong id="pdf-word-local-title">高质量本地转换引擎</strong><span id="pdf-word-local-status">正在检测本地引擎。它会重建段落、图片和 Word 原生公式。</span></div>
    <div class="pdf-word-local-actions"><a class="pdf-word-download-engine" href="{{ '/local-pdf-engine.zip' | relative_url }}" download>下载本地引擎</a><button id="pdf-word-check-local" class="pdf-word-button" type="button">重新检测</button></div>
  </section>
  <details class="pdf-word-browser-fallback">
    <summary>浏览器备用模式</summary>
  <section class="pdf-word-model" aria-labelledby="pdf-word-model-title">
    <div><strong id="pdf-word-model-title">公式模型本地缓存</strong><span id="pdf-word-model-status">首次下载后将保存在当前浏览器，后续无需重新下载。</span></div>
    <div class="pdf-word-model-actions"><label class="pdf-word-skip"><input id="pdf-word-skip-formulas" type="checkbox"> 仅转换文字</label><a href="https://huggingface.co/onnx-community/TexTeller3-ONNX" target="_blank" rel="noopener">模型下载页</a><button id="pdf-word-preload" class="pdf-word-button" type="button">后台加载模型</button></div>
  </section>
  </details>
  <label class="pdf-word-upload">
    <span><strong>选择 PDF 文件</strong><span>文字型 PDF 直接解析；扫描页自动进行中英文 OCR。文件只在浏览器本地处理。</span></span>
    <input id="pdf-word-file" type="file" accept="application/pdf,.pdf">
  </label>
  <div class="pdf-word-options">
    <div class="pdf-word-field"><label for="pdf-word-quality">识别清晰度</label><select id="pdf-word-quality"><option value="1.6">标准</option><option value="2" selected>高清</option><option value="2.5">超清</option></select></div>
    <div class="pdf-word-mode-note"><strong>输出格式</strong><span id="pdf-word-active-engine">优先使用本地引擎：可编辑段落 + 图片 + Word 原生公式</span></div>
    <button id="pdf-word-convert" class="pdf-word-button" type="button" disabled>转换所选页面</button>
  </div>
  <div id="pdf-word-progress" class="pdf-word-progress" hidden>
    <div class="pdf-word-progress-head"><strong id="pdf-word-progress-title">准备转换</strong><span id="pdf-word-progress-value">0%</span></div>
    <div class="pdf-word-track"><span id="pdf-word-progress-bar"></span></div><p id="pdf-word-progress-detail"></p>
  </div>
  <div id="pdf-word-workspace" class="pdf-word-workspace" hidden>
    <section class="pdf-word-panel"><div class="pdf-word-pages-head"><h2>选择转换页面</h2><span id="pdf-word-selection-count">尚未选择 PDF</span></div><div class="pdf-word-page-tools"><button id="pdf-word-select-all" type="button">全选</button><button id="pdf-word-select-none" type="button">清空</button><input id="pdf-word-page-range" type="text" inputmode="numeric" placeholder="例如 1,3,5-8"><button id="pdf-word-apply-range" type="button">应用页码</button></div><div id="pdf-word-pages" class="pdf-word-pages"></div></section>
    <aside class="pdf-word-panel"><h2>数学公式 LaTeX</h2><div id="pdf-word-formulas" class="pdf-word-formulas"><div class="pdf-word-empty">正在定位并识别数学公式...</div></div><div class="pdf-word-side-actions"><button id="pdf-word-copy-all" class="pdf-word-button" type="button">复制全部</button><button id="pdf-word-download-tex" class="pdf-word-button" type="button">下载 .tex</button></div></aside>
  </div>
</div>

<script type="module">
(() => {
  const modelCacheKey = 'pdf-word-formula-model-v1';
  const localEngineUrl = 'http://127.0.0.1:8765';
  const state = { file: null, pdf: null, pages: [], formulas: [], selectedPages: new Set(), localEngineReady: false, formulaWorker: null, workerRequests: new Map(), nextRequestId: 1, workerReady: false, formulaBackend: '' };
  const elements = {
    file: document.querySelector('#pdf-word-file'), quality: document.querySelector('#pdf-word-quality'), convert: document.querySelector('#pdf-word-convert'),
    localStatus: document.querySelector('#pdf-word-local-status'), checkLocal: document.querySelector('#pdf-word-check-local'), activeEngine: document.querySelector('#pdf-word-active-engine'), preload: document.querySelector('#pdf-word-preload'), modelStatus: document.querySelector('#pdf-word-model-status'), skipFormulas: document.querySelector('#pdf-word-skip-formulas'),
    progress: document.querySelector('#pdf-word-progress'), progressTitle: document.querySelector('#pdf-word-progress-title'), progressValue: document.querySelector('#pdf-word-progress-value'),
    progressBar: document.querySelector('#pdf-word-progress-bar'), progressDetail: document.querySelector('#pdf-word-progress-detail'), workspace: document.querySelector('#pdf-word-workspace'),
    pages: document.querySelector('#pdf-word-pages'), selectionCount: document.querySelector('#pdf-word-selection-count'), selectAll: document.querySelector('#pdf-word-select-all'), selectNone: document.querySelector('#pdf-word-select-none'), pageRange: document.querySelector('#pdf-word-page-range'), applyRange: document.querySelector('#pdf-word-apply-range'),
    formulas: document.querySelector('#pdf-word-formulas'), copyAll: document.querySelector('#pdf-word-copy-all'), downloadTex: document.querySelector('#pdf-word-download-tex')
  };
  let pdfjsPromise;
  async function getPdfJs() {
    if (!pdfjsPromise) pdfjsPromise = import('https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.min.mjs').then((pdfjs) => { pdfjs.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs'; return pdfjs; });
    return pdfjsPromise;
  }
  function progress(title, value, detail = '') {
    elements.progress.hidden = false; elements.progressTitle.textContent = title; elements.progressValue.textContent = `${Math.round(value)}%`;
    elements.progressBar.style.width = `${Math.max(0, Math.min(100, value))}%`; elements.progressDetail.textContent = detail;
  }
  async function checkLocalEngine() {
    elements.checkLocal.disabled = true;
    const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), 2200);
    try {
      const response = await fetch(`${localEngineUrl}/status`, { signal: controller.signal, cache: 'no-store' });
      if (!response.ok) throw new Error('服务未就绪');
      const data = await response.json(); state.localEngineReady = Boolean(data.ready);
      elements.localStatus.textContent = `本地引擎已连接（${data.engine || '高质量解析'}）。转换将在电脑本地完成。`;
      elements.localStatus.closest('.pdf-word-local').classList.add('is-ready');
      elements.activeEngine.textContent = '本地高质量模式：段落重排 + 图片 + Word 原生公式';
      elements.checkLocal.textContent = '已连接';
    } catch (_) {
      state.localEngineReady = false;
      elements.localStatus.textContent = '尚未连接。首次使用请下载并解压，双击 install.bat；以后只需双击 start.bat。';
      elements.localStatus.closest('.pdf-word-local').classList.remove('is-ready');
      elements.activeEngine.textContent = '当前使用浏览器备用模式；连接本地引擎后排版与公式质量更高';
      elements.checkLocal.textContent = '重新检测';
    } finally { clearTimeout(timer); elements.checkLocal.disabled = false; }
  }
  function selectedPageSpec() { return [...state.selectedPages].sort((a, b) => a - b).join(','); }
  async function convertWithLocalEngine() {
    progress('本地引擎正在解析', 18, '正在提取段落、图片和数学公式，请勿关闭本地引擎窗口。');
    const body = new FormData(); body.append('file', state.file); body.append('pages', selectedPageSpec());
    const response = await fetch(`${localEngineUrl}/convert`, { method: 'POST', body });
    if (!response.ok) { let message = `本地转换失败（${response.status}）`; try { message = (await response.json()).detail || message; } catch (_) {} throw new Error(message); }
    const formulaHeader = response.headers.get('X-PDF-Formulas'); state.formulas = [];
    if (formulaHeader) { try { state.formulas = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(formulaHeader), (char) => char.charCodeAt(0)))).map((item, index) => ({ ...item, index })); } catch (_) {} }
    renderFormulas();
    progress('正在生成 Word', 88, '正在写入可编辑段落、图片和原生公式对象...');
    const blob = await response.blob(); const anchor = document.createElement('a'); anchor.href = URL.createObjectURL(blob);
    anchor.download = `${state.file.name.replace(/\.pdf$/i, '')}-editable.docx`; anchor.click(); setTimeout(() => URL.revokeObjectURL(anchor.href), 3000);
    progress('Word 已生成', 100, '文档已重新排版，正文、图片和公式均可继续编辑。');
  }
  function looksMathematical(text) {
    const value = text.trim(); if (value.length < 2 || value.length > 420) return false;
    const operators = (value.match(/[=<>≤≥≠≈∑∏∫√±×÷^_{}()[\]]/g) || []).length; const greek = (value.match(/[α-ωΑ-Ω]/g) || []).length;
    const words = (value.match(/[A-Za-z]{5,}/g) || []).length; return operators + greek >= 2 || ((/[=∑∫√]/.test(value)) && words <= 3);
  }
  function sanitizeText(value) { return String(value || '').replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g, '').replace(/\u00ad/g, '').trim(); }
  function groupPdfLines(items, viewport, pdfjs) {
    const rows = [];
    items.forEach((item) => {
      if (!item.str?.trim()) return; const point = pdfjs.Util.transform(viewport.transform, item.transform); const y = point[5];
      let row = rows.find((candidate) => Math.abs(candidate.y - y) <= 4); if (!row) { row = { y, items: [] }; rows.push(row); }
      row.items.push({ text: item.str, x: point[4], y, width: Math.max(2, item.width * viewport.scale), height: Math.max(10, Math.hypot(point[2], point[3])) });
    });
    const lines = []; rows.forEach((row) => { row.items.sort((a, b) => a.x - b.x); let segment = [];
      const flush = () => { if (!segment.length) return; const x = segment[0].x; const end = Math.max(...segment.map((item) => item.x + item.width)); const text = sanitizeText(segment.map((item) => item.text).join(' ').replace(/\s+/g, ' ')); if (text) lines.push({ y: row.y, x, width: end - x, items: segment, text }); segment = []; };
      row.items.forEach((item) => { const previous = segment.at(-1); const gap = previous ? item.x - (previous.x + previous.width) : 0; const crossesColumns = previous && previous.x < viewport.width / 2 && item.x >= viewport.width / 2; if (previous && (gap > viewport.width * .06 || crossesColumns)) flush(); segment.push(item); }); flush();
    });
    lines.sort((a, b) => a.y - b.y || a.x - b.x); const midpoint = viewport.width / 2; const pairedRows = lines.filter((line) => line.x < midpoint).map((line) => line.y).filter((y) => lines.some((other) => other.x >= midpoint && Math.abs(other.y - y) <= 5));
    const columnStart = pairedRows.find((y) => pairedRows.filter((next) => next >= y && next <= y + viewport.height * .18).length >= 4); if (columnStart === undefined) return lines;
    const preamble = lines.filter((line) => line.y < columnStart - 5); const columns = lines.filter((line) => line.y >= columnStart - 5); const left = columns.filter((line) => line.x < midpoint).sort((a, b) => a.y - b.y || a.x - b.x); const right = columns.filter((line) => line.x >= midpoint).sort((a, b) => a.y - b.y || a.x - b.x); return [...preamble, ...left, ...right];
  }
  function cropLine(canvas, line) {
    const minX = Math.max(0, Math.min(...line.items.map((item) => item.x)) - 20); const maxX = Math.min(canvas.width, Math.max(...line.items.map((item) => item.x + item.width)) + 20);
    const minY = Math.max(0, Math.min(...line.items.map((item) => item.y - item.height * 1.3)) - 12); const maxY = Math.min(canvas.height, Math.max(...line.items.map((item) => item.y + item.height * .6)) + 12);
    const crop = document.createElement('canvas'); crop.width = Math.max(4, Math.round(maxX - minX)); crop.height = Math.max(4, Math.round(maxY - minY));
    crop.getContext('2d', { alpha: false }).drawImage(canvas, minX, minY, crop.width, crop.height, 0, 0, crop.width, crop.height); return crop;
  }
  function getFormulaWorker() {
    if (state.formulaWorker) return state.formulaWorker;
    const source = `let recognizer=null,RawImage=null,backend='';const report=(id)=>(event)=>self.postMessage({type:'progress',id,event});async function load(id){if(recognizer)return backend;const module=await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.2/+esm');RawImage=module.RawImage;module.env.allowLocalModels=false;module.env.useBrowserCache=true;if(self.navigator?.gpu){try{recognizer=await module.pipeline('image-to-text','onnx-community/TexTeller3-ONNX',{device:'webgpu',dtype:'q4f16',progress_callback:report(id)});backend='WebGPU';self.postMessage({type:'backend',id,value:backend});return backend}catch(error){recognizer=null;self.postMessage({type:'fallback',id})}}let lastError;for(let attempt=1;attempt<=3;attempt++){try{recognizer=await module.pipeline('image-to-text','onnx-community/TexTeller3-ONNX',{device:'wasm',dtype:'q4',progress_callback:report(id)});backend='WASM CPU';self.postMessage({type:'backend',id,value:backend});return backend}catch(error){lastError=error;self.postMessage({type:'retry',id,attempt:Math.min(attempt+1,3)});await new Promise((resolve)=>setTimeout(resolve,1200*attempt))}}throw lastError}self.onmessage=async({data})=>{const{id,type}=data;try{const activeBackend=await load(id);if(type==='load'){self.postMessage({type:'result',id,value:activeBackend});return}const image=new RawImage(new Uint8ClampedArray(data.pixels),data.width,data.height,1);const output=await recognizer(image,{max_new_tokens:192});self.postMessage({type:'result',id,value:output?.[0]?.generated_text||output?.generated_text||''})}catch(error){self.postMessage({type:'error',id,message:error?.message||String(error)})}};`;
    const url = URL.createObjectURL(new Blob([source], { type: 'text/javascript' })); const worker = new Worker(url, { type: 'module' }); URL.revokeObjectURL(url);
    worker.onmessage = ({ data }) => { if (data.type === 'progress') { if (Number.isFinite(data.event?.progress)) progress('后台下载公式模型', data.event.progress, data.event.file ? `正在下载：${data.event.file}` : '正在下载模型文件...'); return; } if (data.type === 'backend') { state.formulaBackend = data.value; elements.modelStatus.textContent = `公式模型已启用 ${data.value} 加速。`; return; } if (data.type === 'fallback') { elements.modelStatus.textContent = '当前浏览器无法启用 WebGPU，正在切换 CPU 模式。'; return; } if (data.type === 'retry') { progress('重试加载公式模型', 42, `网络中断，正在进行第 ${data.attempt} 次尝试...`); return; } const request = state.workerRequests.get(data.id); if (!request) return; clearTimeout(request.timer); state.workerRequests.delete(data.id); data.type === 'error' ? request.reject(new Error(data.message)) : request.resolve(data.value); };
    worker.onerror = (event) => { state.workerRequests.forEach((request) => { clearTimeout(request.timer); request.reject(new Error(event.message || '公式模型后台线程异常')); }); state.workerRequests.clear(); state.formulaWorker = null; };
    state.formulaWorker = worker; return worker;
  }
  function formulaWorkerRequest(type, payload = {}, transfer = []) {
    const id = state.nextRequestId++; const worker = getFormulaWorker(); return new Promise((resolve, reject) => { const timer = setTimeout(() => { state.workerRequests.delete(id); worker.terminate(); state.formulaWorker = null; state.workerReady = false; reject(new Error('公式模型加载超时，请重试或选择“仅转换文字”')); }, 300000); state.workerRequests.set(id, { resolve, reject, timer }); worker.postMessage({ id, type, ...payload }, transfer); });
  }
  async function loadFormulaRecognizer() { if (state.workerReady) return state.formulaBackend; const cached = localStorage.getItem(modelCacheKey); progress(cached ? '从本地缓存启动模型' : '首次下载数学公式模型', 2, cached ? '无需重复下载，正在初始化本地模型。' : '正在检测 WebGPU，页面仍可继续操作。'); state.formulaBackend = await formulaWorkerRequest('load'); state.workerReady = true; localStorage.setItem(modelCacheKey, JSON.stringify({ backend: state.formulaBackend, cachedAt: Date.now() })); return state.formulaBackend; }
  function cleanLatex(value) { return sanitizeText(value).replace(/^\s*\$+|\$+\s*$/g, '').replace(/^\\\[|\\\]$/g, '').replace(/\s+/g, ' ').trim(); }
  function embeddedMathToLatex(source) {
    const symbols = { 'α':'\\alpha', 'β':'\\beta', 'γ':'\\gamma', 'δ':'\\delta', 'ε':'\\epsilon', 'θ':'\\theta', 'λ':'\\lambda', 'μ':'\\mu', 'π':'\\pi', 'ρ':'\\rho', 'σ':'\\sigma', 'τ':'\\tau', 'φ':'\\phi', 'ω':'\\omega', 'Σ':'\\Sigma', '×':'\\times', '÷':'\\div', '±':'\\pm', '≤':'\\leq', '≥':'\\geq', '≠':'\\neq', '≈':'\\approx', '∞':'\\infty', '∂':'\\partial', '∇':'\\nabla', '∑':'\\sum', '∏':'\\prod', '∫':'\\int', '→':'\\to', '∈':'\\in', '⊂':'\\subset' };
    const superscripts = { '⁰':'0', '¹':'1', '²':'2', '³':'3', '⁴':'4', '⁵':'5', '⁶':'6', '⁷':'7', '⁸':'8', '⁹':'9', '⁺':'+', '⁻':'-', 'ⁿ':'n' }; const subscripts = { '₀':'0', '₁':'1', '₂':'2', '₃':'3', '₄':'4', '₅':'5', '₆':'6', '₇':'7', '₈':'8', '₉':'9' };
    let value = sanitizeText(source).replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿ]+/g, (part) => `^{${[...part].map((char) => superscripts[char]).join('')}}`).replace(/[₀₁₂₃₄₅₆₇₈₉]+/g, (part) => `_{${[...part].map((char) => subscripts[char]).join('')}}`); Object.entries(symbols).forEach(([symbol, latex]) => { value = value.split(symbol).join(` ${latex} `); }); return value.replace(/\s+/g, ' ').trim();
  }
  function isUsableLatex(latex, source) { if (!latex || latex.length > Math.max(160, source.length * 6)) return false; if (/(.)\1{9,}/.test(latex) || /(.{2,8})\1{7,}/.test(latex)) return false; const opens = (latex.match(/\{/g) || []).length; const closes = (latex.match(/\}/g) || []).length; return Math.abs(opens - closes) <= 1 && !/begin(?:cdot|bullet|text)/i.test(latex); }
  function toGrayscaleImage(canvas) {
    const rgba = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data; const gray = new Uint8ClampedArray(canvas.width * canvas.height);
    for (let source = 0, target = 0; source < rgba.length; source += 4, target++) gray[target] = Math.round(rgba[source] * .299 + rgba[source + 1] * .587 + rgba[source + 2] * .114);
    return { data: gray, width: canvas.width, height: canvas.height };
  }
  async function recognizeFormula(canvas, pageNumber, sourceText) {
    await loadFormulaRecognizer(); const image = toGrayscaleImage(canvas); const result = await formulaWorkerRequest('recognize', { pixels: image.data.buffer, width: image.width, height: image.height }, [image.data.buffer]); const latex = cleanLatex(result);
    const safeLatex = isUsableLatex(latex, sourceText) ? latex : embeddedMathToLatex(sourceText); if (!safeLatex) return null; const formula = { latex: safeLatex, pageNumber, index: state.formulas.length }; state.formulas.push(formula); return formula;
  }
  async function ocrScannedPage(canvas) {
    progress('识别扫描页正文', 24, '正在加载中英文正文 OCR...'); const module = await import('https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/+esm'); const Tesseract = module.default || module;
    const result = await Tesseract.recognize(canvas, 'eng+chi_sim');
    return (result.data?.lines || []).map((line) => ({ text: sanitizeText(line.text.replace(/\s+/g, ' ')), items: [{ x: line.bbox.x0, y: line.bbox.y1, width: line.bbox.x1 - line.bbox.x0, height: line.bbox.y1 - line.bbox.y0 }] })).filter((line) => line.text);
  }
  function renderFormulas() {
    if (!state.formulas.length) { elements.formulas.innerHTML = '<div class="pdf-word-empty">没有识别到明确的数学公式。普通正文不会被伪装成 LaTeX。</div>'; return; }
    elements.formulas.innerHTML = '';
    state.formulas.forEach((item, index) => {
      const card = document.createElement('div'); card.className = 'pdf-word-formula'; card.innerHTML = `<div class="pdf-word-formula-head"><span>第 ${item.pageNumber} 页 · 公式 ${index + 1}</span><button class="pdf-word-copy" type="button">复制</button></div><textarea class="pdf-word-latex"></textarea><div class="pdf-word-preview"></div>`;
      const textarea = card.querySelector('textarea'); const preview = card.querySelector('.pdf-word-preview'); textarea.value = item.latex;
      const draw = () => { item.latex = textarea.value; try { katex.render(item.latex, preview, { throwOnError: false, displayMode: true }); } catch (_) { preview.textContent = item.latex; } };
      textarea.addEventListener('input', draw); card.querySelector('button').addEventListener('click', () => navigator.clipboard.writeText(textarea.value)); draw(); elements.formulas.appendChild(card);
    });
  }
  function updateSelection() {
    const count = state.selectedPages.size; const total = state.pdf?.numPages || 0; elements.selectionCount.textContent = `已选择 ${count} / ${total} 页`; elements.convert.disabled = count === 0;
    elements.pages.querySelectorAll('.pdf-word-page-card').forEach((card) => card.classList.toggle('is-selected', card.querySelector('input').checked));
  }
  function parsePageRange(value, total) {
    const selected = new Set(); value.split(/[，,\s]+/).filter(Boolean).forEach((part) => { const match = part.match(/^(\d+)(?:-(\d+))?$/); if (!match) return; let start = Number(match[1]); let end = Number(match[2] || match[1]); if (start > end) [start, end] = [end, start]; for (let page = Math.max(1, start); page <= Math.min(total, end); page++) selected.add(page); }); return selected;
  }
  async function loadPdf(file) {
    const pdfjs = await getPdfJs(); progress('拆分 PDF 页面', 3, '正在生成页面缩略图...'); state.pdf = await pdfjs.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise;
    state.pages = []; state.formulas = []; state.selectedPages = new Set(); elements.pages.innerHTML = ''; elements.workspace.hidden = false; elements.formulas.innerHTML = '<div class="pdf-word-empty">转换后将在这里显示所选页面中的数学公式。</div>';
    for (let number = 1; number <= state.pdf.numPages; number++) {
      progress(`拆分第 ${number} / ${state.pdf.numPages} 页`, number / state.pdf.numPages * 100, '只生成缩略图，尚未执行正文和公式识别。'); const page = await state.pdf.getPage(number); const viewport = page.getViewport({ scale: .42 });
      const canvas = document.createElement('canvas'); canvas.width = Math.ceil(viewport.width); canvas.height = Math.ceil(viewport.height); await page.render({ canvasContext: canvas.getContext('2d', { alpha: false }), viewport }).promise;
      const card = document.createElement('label'); card.className = 'pdf-word-page-card is-selected'; const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.checked = true; checkbox.value = number; const caption = document.createElement('span'); caption.textContent = `第 ${number} 页`; card.append(checkbox, canvas, caption); elements.pages.appendChild(card); state.selectedPages.add(number);
      checkbox.addEventListener('change', () => { checkbox.checked ? state.selectedPages.add(number) : state.selectedPages.delete(number); updateSelection(); });
    }
    updateSelection(); progress('页面拆分完成', 100, '请选择需要转换的页面，再点击“转换所选页面”。');
  }
  async function parseSelectedPages() {
    const pdfjs = await getPdfJs(); const selected = [...state.selectedPages].sort((a, b) => a - b); state.pages = []; state.formulas = []; const scale = Number(elements.quality.value);
    for (let index = 0; index < selected.length; index++) {
      const number = selected[index]; progress(`转换第 ${number} 页`, index / selected.length * 72, `正在处理所选页面 ${index + 1} / ${selected.length}`); const page = await state.pdf.getPage(number); const viewport = page.getViewport({ scale });
      const canvas = document.createElement('canvas'); canvas.width = Math.ceil(viewport.width); canvas.height = Math.ceil(viewport.height); await page.render({ canvasContext: canvas.getContext('2d', { alpha: false }), viewport }).promise;
      const text = await page.getTextContent(); let lines = groupPdfLines(text.items, viewport, pdfjs); if (!lines.length) lines = await ocrScannedPage(canvas); const blocks = [];
      for (const line of lines) {
        if (!elements.skipFormulas.checked && looksMathematical(line.text) && state.formulas.length < 30) { try { const formula = await recognizeFormula(cropLine(canvas, line), number, line.text); if (formula) { blocks.push({ type: 'formula', formulaIndex: formula.index }); continue; } } catch (error) { console.warn('Formula OCR failed', error); const latex = embeddedMathToLatex(line.text); if (latex) { const formula = { latex, pageNumber: number, index: state.formulas.length }; state.formulas.push(formula); blocks.push({ type: 'formula', formulaIndex: formula.index }); continue; } } }
        blocks.push({ type: 'text', text: line.text });
      }
      state.pages.push({ number, blocks });
    }
    renderFormulas(); progress('所选页面解析完成', 74, `已解析 ${selected.length} 页，识别到 ${state.formulas.length} 条数学公式。`);
  }
  const xmlEscape = (value) => sanitizeText(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const commandMap = { alpha:'α', beta:'β', gamma:'γ', delta:'δ', epsilon:'ε', theta:'θ', lambda:'λ', mu:'μ', pi:'π', rho:'ρ', sigma:'σ', tau:'τ', phi:'φ', omega:'ω', Gamma:'Γ', Delta:'Δ', Lambda:'Λ', Sigma:'Σ', Phi:'Φ', Omega:'Ω', times:'×', cdot:'·', div:'÷', pm:'±', le:'≤', leq:'≤', ge:'≥', geq:'≥', neq:'≠', approx:'≈', infty:'∞', partial:'∂', nabla:'∇', sum:'∑', prod:'∏', int:'∫', to:'→' };
  function latexToOmml(latex) {
    const source = cleanLatex(latex).replace(/\\left|\\right/g, ''); let cursor = 0; const run = (text) => `<m:r><m:t xml:space="preserve">${xmlEscape(text)}</m:t></m:r>`;
    const readCommand = () => { cursor++; const match = source.slice(cursor).match(/^[A-Za-z]+/); if (!match) return source[cursor++] || ''; cursor += match[0].length; return match[0]; };
    function sequence(stop = '') { let output = ''; while (cursor < source.length && (!stop || source[cursor] !== stop)) output += atom(); if (stop && source[cursor] === stop) cursor++; return output; }
    function argument() { if (source[cursor] === '{') { cursor++; return sequence('}'); } return atom(false); }
    function atom(withScripts = true) {
      if (cursor >= source.length) return ''; let base = '';
      if (source[cursor] === '{') { cursor++; base = sequence('}'); }
      else if (source[cursor] === '\\') { const command = readCommand(); if (command === 'frac') base = `<m:f><m:num>${argument()}</m:num><m:den>${argument()}</m:den></m:f>`; else if (command === 'sqrt') base = `<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:e>${argument()}</m:e></m:rad>`; else if (['text','mathrm','mathbf','mathit'].includes(command)) base = argument(); else base = run(commandMap[command] || `\\${command}`); }
      else base = run(source[cursor++]); if (!withScripts) return base; let sub = '', sup = '';
      while (source[cursor] === '_' || source[cursor] === '^') { const type = source[cursor++]; const value = argument(); if (type === '_') sub = value; else sup = value; }
      if (sub && sup) return `<m:sSubSup><m:e>${base}</m:e><m:sub>${sub}</m:sub><m:sup>${sup}</m:sup></m:sSubSup>`;
      if (sub) return `<m:sSub><m:e>${base}</m:e><m:sub>${sub}</m:sub></m:sSub>`; if (sup) return `<m:sSup><m:e>${base}</m:e><m:sup>${sup}</m:sup></m:sSup>`; return base;
    }
    return `<m:oMath>${sequence()}</m:oMath>`;
  }
  async function injectWordEquations(blob) {
    const zip = await window.JSZip.loadAsync(blob); const entry = zip.file('word/document.xml'); const xml = new DOMParser().parseFromString(await entry.async('text'), 'application/xml');
    const wNamespace = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main';
    Array.from(xml.getElementsByTagNameNS(wNamespace, 't')).forEach((node) => {
      const match = node.textContent.match(/^\[\[FORMULA_(\d+)\]\]$/); if (!match) return; const formula = state.formulas[Number(match[1])]; if (!formula) return;
      const wrapper = new DOMParser().parseFromString(`<root xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">${latexToOmml(formula.latex)}</root>`, 'application/xml');
      node.parentNode.parentNode.replaceChild(xml.importNode(wrapper.documentElement.firstElementChild, true), node.parentNode);
    });
    zip.file('word/document.xml', new XMLSerializer().serializeToString(xml)); return zip.generateAsync({ type: 'blob', mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
  }
  async function exportDocx() {
    if (!state.pages.length || !window.docx) return; elements.convert.disabled = true; progress('生成可编辑 Word', 8); const { Document, Packer, Paragraph, PageBreak, TextRun } = window.docx; const children = [];
    state.pages.forEach((page, pageIndex) => {
      page.blocks.forEach((block) => { if (block.type === 'formula') children.push(new Paragraph({ children: [new TextRun(`[[FORMULA_${block.formulaIndex}]]`)], spacing: { before: 100, after: 100 } })); else children.push(new Paragraph({ children: [new TextRun({ text: sanitizeText(block.text), font: 'Microsoft YaHei', size: 22 })], spacing: { after: 80, line: 300 } })); });
      if (pageIndex < state.pages.length - 1) children.push(new Paragraph({ children: [new PageBreak()] }));
    });
    const doc = new Document({ sections: [{ properties: { page: { margin: { top: 720, right: 720, bottom: 720, left: 720 } } }, children }] });
    progress('写入 Word 原生公式', 76, '正在把 LaTeX 转换为可编辑 OMML 公式对象...'); const blob = await injectWordEquations(await Packer.toBlob(doc));
    const anchor = document.createElement('a'); anchor.href = URL.createObjectURL(blob); anchor.download = `${state.file.name.replace(/\.pdf$/i, '')}-editable.docx`; anchor.click(); setTimeout(() => URL.revokeObjectURL(anchor.href), 3000); progress('Word 已生成', 100, '正文和公式均可在 Word 中继续编辑。'); elements.convert.disabled = false;
  }
  async function convertSelectedPages() { if (!state.selectedPages.size) return; elements.convert.disabled = true; try { if (state.localEngineReady) await convertWithLocalEngine(); else { await parseSelectedPages(); await exportDocx(); } } catch (error) { console.error(error); progress('转换失败', 0, error.message || '所选页面转换失败'); } finally { elements.convert.disabled = state.selectedPages.size === 0; } }
  elements.file.addEventListener('change', async () => { const file = elements.file.files[0]; if (!file) return; state.file = file; elements.convert.disabled = true; try { await loadPdf(file); } catch (error) { console.error(error); progress('转换失败', 0, error.message || 'PDF 读取失败'); } });
  elements.preload.addEventListener('click', async () => {
    elements.preload.disabled = true; elements.preload.textContent = '后台加载中...'; elements.modelStatus.textContent = '模型在后台下载，页面仍可操作；请保持当前页面打开。';
    try { if (navigator.storage?.persist) await navigator.storage.persist(); const backend = await loadFormulaRecognizer(); elements.preload.textContent = '模型已缓存'; elements.modelStatus.textContent = `公式模型已就绪（${backend}），以后打开本页面无需重新下载。`; progress('公式模型已就绪', 100, `模型已持久缓存在当前浏览器，推理后端：${backend}。`); }
    catch (error) { console.error(error); elements.preload.disabled = false; elements.preload.textContent = '重新加载模型'; elements.modelStatus.textContent = '下载未完成，请检查网络后重新加载。'; progress('模型加载失败', 0, error.message || '模型下载失败'); }
  });
  elements.selectAll.addEventListener('click', () => { state.selectedPages = new Set(Array.from({ length: state.pdf?.numPages || 0 }, (_, index) => index + 1)); elements.pages.querySelectorAll('input').forEach((input) => { input.checked = true; }); updateSelection(); });
  elements.selectNone.addEventListener('click', () => { state.selectedPages.clear(); elements.pages.querySelectorAll('input').forEach((input) => { input.checked = false; }); updateSelection(); });
  elements.applyRange.addEventListener('click', () => { if (!state.pdf) return; state.selectedPages = parsePageRange(elements.pageRange.value, state.pdf.numPages); elements.pages.querySelectorAll('input').forEach((input) => { input.checked = state.selectedPages.has(Number(input.value)); }); updateSelection(); });
  elements.pageRange.addEventListener('keydown', (event) => { if (event.key === 'Enter') elements.applyRange.click(); }); elements.convert.addEventListener('click', convertSelectedPages);
  elements.checkLocal.addEventListener('click', checkLocalEngine);
  elements.copyAll.addEventListener('click', () => navigator.clipboard.writeText(state.formulas.map((item) => item.latex).join('\n\n')));
  elements.downloadTex.addEventListener('click', () => { const blob = new Blob([state.formulas.map((item) => `\\[\n${item.latex}\n\\]`).join('\n\n')], { type: 'text/plain;charset=utf-8' }); const anchor = document.createElement('a'); anchor.href = URL.createObjectURL(blob); anchor.download = `${state.file?.name.replace(/\.pdf$/i, '') || 'formulas'}.tex`; anchor.click(); setTimeout(() => URL.revokeObjectURL(anchor.href), 2000); });
  async function initializeCachedModel() {
    let cached = Boolean(localStorage.getItem(modelCacheKey)); if (!cached && 'caches' in window) { const base = 'https://huggingface.co/onnx-community/TexTeller3-ONNX/resolve/main/onnx/'; cached = Boolean(await caches.match(`${base}decoder_model_merged_q4.onnx`) || await caches.match(`${base}decoder_model_merged_q4f16.onnx`)); if (cached) localStorage.setItem(modelCacheKey, JSON.stringify({ detectedAt: Date.now() })); }
    if (!cached) return; elements.preload.textContent = '从本地缓存启动'; elements.modelStatus.textContent = '检测到本地模型缓存，页面空闲时将自动启动，不会重复下载。'; const warmup = async () => { if (state.workerReady) return; elements.preload.disabled = true; try { const backend = await loadFormulaRecognizer(); elements.preload.textContent = '模型已就绪'; elements.modelStatus.textContent = `已从本地缓存启动（${backend}）。`; } catch (_) { elements.preload.disabled = false; elements.preload.textContent = '重新下载模型'; localStorage.removeItem(modelCacheKey); } }; 'requestIdleCallback' in window ? requestIdleCallback(warmup, { timeout: 2500 }) : setTimeout(warmup, 800);
  }
  checkLocalEngine(); initializeCachedModel().catch(() => {});
})();
</script>
