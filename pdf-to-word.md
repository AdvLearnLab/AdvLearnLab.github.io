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
  <section class="pdf-word-model" aria-labelledby="pdf-word-model-title">
    <div><strong id="pdf-word-model-title">首次使用：先加载公式模型</strong><span id="pdf-word-model-status">模型文件较大，建议先完成下载并缓存，再上传 PDF。</span></div>
    <div class="pdf-word-model-actions"><a href="https://huggingface.co/onnx-community/TexTeller3-ONNX" target="_blank" rel="noopener">模型下载页</a><button id="pdf-word-preload" class="pdf-word-button" type="button">提前加载模型</button></div>
  </section>
  <label class="pdf-word-upload">
    <span><strong>选择 PDF 文件</strong><span>文字型 PDF 直接解析；扫描页自动进行中英文 OCR。文件只在浏览器本地处理。</span></span>
    <input id="pdf-word-file" type="file" accept="application/pdf,.pdf">
  </label>
  <div class="pdf-word-options">
    <div class="pdf-word-field"><label for="pdf-word-quality">识别清晰度</label><select id="pdf-word-quality"><option value="1.6">标准</option><option value="2" selected>高清</option><option value="2.5">超清</option></select></div>
    <div class="pdf-word-mode-note"><strong>输出格式</strong><span>可编辑文字 + Word 原生公式</span></div>
    <button id="pdf-word-convert" class="pdf-word-button" type="button" disabled>转换并下载 Word</button>
  </div>
  <div id="pdf-word-progress" class="pdf-word-progress" hidden>
    <div class="pdf-word-progress-head"><strong id="pdf-word-progress-title">准备转换</strong><span id="pdf-word-progress-value">0%</span></div>
    <div class="pdf-word-track"><span id="pdf-word-progress-bar"></span></div><p id="pdf-word-progress-detail"></p>
  </div>
  <div id="pdf-word-workspace" class="pdf-word-workspace" hidden>
    <section class="pdf-word-panel"><h2>页面预览</h2><div id="pdf-word-pages" class="pdf-word-pages"></div></section>
    <aside class="pdf-word-panel"><h2>数学公式 LaTeX</h2><div id="pdf-word-formulas" class="pdf-word-formulas"><div class="pdf-word-empty">正在定位并识别数学公式...</div></div><div class="pdf-word-side-actions"><button id="pdf-word-copy-all" class="pdf-word-button" type="button">复制全部</button><button id="pdf-word-download-tex" class="pdf-word-button" type="button">下载 .tex</button></div></aside>
  </div>
</div>

<script type="module">
(() => {
  const state = { file: null, pdf: null, pages: [], formulas: [], recognizer: null, RawImage: null };
  const elements = {
    file: document.querySelector('#pdf-word-file'), quality: document.querySelector('#pdf-word-quality'), convert: document.querySelector('#pdf-word-convert'),
    preload: document.querySelector('#pdf-word-preload'), modelStatus: document.querySelector('#pdf-word-model-status'),
    progress: document.querySelector('#pdf-word-progress'), progressTitle: document.querySelector('#pdf-word-progress-title'), progressValue: document.querySelector('#pdf-word-progress-value'),
    progressBar: document.querySelector('#pdf-word-progress-bar'), progressDetail: document.querySelector('#pdf-word-progress-detail'), workspace: document.querySelector('#pdf-word-workspace'),
    pages: document.querySelector('#pdf-word-pages'), formulas: document.querySelector('#pdf-word-formulas'), copyAll: document.querySelector('#pdf-word-copy-all'), downloadTex: document.querySelector('#pdf-word-download-tex')
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
  function looksMathematical(text) {
    const value = text.trim(); if (value.length < 2 || value.length > 420) return false;
    const operators = (value.match(/[=<>≤≥≠≈∑∏∫√±×÷^_{}()[\]]/g) || []).length; const greek = (value.match(/[α-ωΑ-Ω]/g) || []).length;
    const words = (value.match(/[A-Za-z]{5,}/g) || []).length; return operators + greek >= 2 || ((/[=∑∫√]/.test(value)) && words <= 3);
  }
  function groupPdfLines(items, viewport, pdfjs) {
    const rows = [];
    items.forEach((item) => {
      if (!item.str?.trim()) return; const point = pdfjs.Util.transform(viewport.transform, item.transform); const y = point[5];
      let row = rows.find((candidate) => Math.abs(candidate.y - y) <= 4); if (!row) { row = { y, items: [] }; rows.push(row); }
      row.items.push({ text: item.str, x: point[4], y, width: Math.max(2, item.width * viewport.scale), height: Math.max(10, Math.hypot(point[2], point[3])) });
    });
    return rows.sort((a, b) => a.y - b.y).map((row) => { row.items.sort((a, b) => a.x - b.x); row.text = row.items.map((item) => item.text).join(' ').replace(/\s+/g, ' ').trim(); return row; }).filter((row) => row.text);
  }
  function cropLine(canvas, line) {
    const minX = Math.max(0, Math.min(...line.items.map((item) => item.x)) - 20); const maxX = Math.min(canvas.width, Math.max(...line.items.map((item) => item.x + item.width)) + 20);
    const minY = Math.max(0, Math.min(...line.items.map((item) => item.y - item.height * 1.3)) - 12); const maxY = Math.min(canvas.height, Math.max(...line.items.map((item) => item.y + item.height * .6)) + 12);
    const crop = document.createElement('canvas'); crop.width = Math.max(4, Math.round(maxX - minX)); crop.height = Math.max(4, Math.round(maxY - minY));
    crop.getContext('2d', { alpha: false }).drawImage(canvas, minX, minY, crop.width, crop.height, 0, 0, crop.width, crop.height); return crop;
  }
  async function loadFormulaRecognizer() {
    if (state.recognizer) return state.recognizer; progress('加载数学公式模型', 42, '首次使用需要下载公式 OCR 模型，之后会由浏览器缓存。');
    const { pipeline, env, RawImage } = await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.2/+esm'); env.allowLocalModels = false; state.RawImage = RawImage;
    const reportDownload = (event) => { if (Number.isFinite(event?.progress)) progress('下载公式模型', event.progress, event.file ? `正在下载：${event.file}` : '正在下载模型文件...'); };
    let lastError; for (let attempt = 1; attempt <= 3; attempt++) { try { state.recognizer = await pipeline('image-to-text', 'onnx-community/TexTeller3-ONNX', { device: 'wasm', dtype: 'q4', progress_callback: reportDownload }); return state.recognizer; } catch (error) { lastError = error; progress('重试加载公式模型', 42, `网络下载中断，正在进行第 ${Math.min(attempt + 1, 3)} 次尝试...`); await new Promise((resolve) => setTimeout(resolve, 1200 * attempt)); } } throw lastError;
  }
  function cleanLatex(value) { return (value || '').replace(/^\s*\$+|\$+\s*$/g, '').replace(/^\\\[|\\\]$/g, '').replace(/\s+/g, ' ').trim(); }
  function toGrayscaleImage(canvas) {
    const rgba = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data; const gray = new Uint8ClampedArray(canvas.width * canvas.height);
    for (let source = 0, target = 0; source < rgba.length; source += 4, target++) gray[target] = Math.round(rgba[source] * .299 + rgba[source + 1] * .587 + rgba[source + 2] * .114);
    return new state.RawImage(gray, canvas.width, canvas.height, 1);
  }
  async function recognizeFormula(canvas, pageNumber) {
    const recognizer = await loadFormulaRecognizer(); const result = await recognizer(toGrayscaleImage(canvas), { max_new_tokens: 384 }); const latex = cleanLatex(result?.[0]?.generated_text || result?.generated_text || '');
    if (!latex) return null; const formula = { latex, pageNumber }; state.formulas.push(formula); return formula;
  }
  async function ocrScannedPage(canvas) {
    progress('识别扫描页正文', 24, '正在加载中英文正文 OCR...'); const module = await import('https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/+esm'); const Tesseract = module.default || module;
    const result = await Tesseract.recognize(canvas, 'eng+chi_sim');
    return (result.data?.lines || []).map((line) => ({ text: line.text.replace(/\s+/g, ' ').trim(), items: [{ x: line.bbox.x0, y: line.bbox.y1, width: line.bbox.x1 - line.bbox.x0, height: line.bbox.y1 - line.bbox.y0 }] })).filter((line) => line.text);
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
  async function loadPdf(file) {
    const pdfjs = await getPdfJs(); progress('读取 PDF', 3); state.pdf = await pdfjs.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise;
    state.pages = []; state.formulas = []; elements.pages.innerHTML = ''; elements.workspace.hidden = false; const scale = Number(elements.quality.value);
    for (let number = 1; number <= state.pdf.numPages; number++) {
      progress(`解析第 ${number} / ${state.pdf.numPages} 页`, 5 + number / state.pdf.numPages * 30); const page = await state.pdf.getPage(number); const viewport = page.getViewport({ scale });
      const canvas = document.createElement('canvas'); canvas.width = Math.ceil(viewport.width); canvas.height = Math.ceil(viewport.height); await page.render({ canvasContext: canvas.getContext('2d', { alpha: false }), viewport }).promise; elements.pages.appendChild(canvas);
      const text = await page.getTextContent(); let lines = groupPdfLines(text.items, viewport, pdfjs); if (lines.length < 2) lines = await ocrScannedPage(canvas); const blocks = [];
      for (const line of lines) {
        if (looksMathematical(line.text) && state.formulas.length < 60) {
          try { const formula = await recognizeFormula(cropLine(canvas, line), number); if (formula) { blocks.push({ type: 'formula', formula }); continue; } } catch (error) { console.warn('Formula OCR failed', error); }
        }
        blocks.push({ type: 'text', text: line.text });
      }
      state.pages.push({ number, blocks });
    }
    renderFormulas(); progress('结构化解析完成', 100, `正文可编辑，识别到 ${state.formulas.length} 条数学公式。`); elements.convert.disabled = false;
  }
  const xmlEscape = (value) => String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
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
      page.blocks.forEach((block) => { if (block.type === 'formula') { const index = state.formulas.indexOf(block.formula); children.push(new Paragraph({ children: [new TextRun(`[[FORMULA_${index}]]`)], spacing: { before: 100, after: 100 } })); } else children.push(new Paragraph({ children: [new TextRun({ text: block.text, font: 'Microsoft YaHei', size: 22 })], spacing: { after: 80, line: 300 } })); });
      if (pageIndex < state.pages.length - 1) children.push(new Paragraph({ children: [new PageBreak()] }));
    });
    const doc = new Document({ sections: [{ properties: { page: { margin: { top: 720, right: 720, bottom: 720, left: 720 } } }, children }] });
    progress('写入 Word 原生公式', 76, '正在把 LaTeX 转换为可编辑 OMML 公式对象...'); const blob = await injectWordEquations(await Packer.toBlob(doc));
    const anchor = document.createElement('a'); anchor.href = URL.createObjectURL(blob); anchor.download = `${state.file.name.replace(/\.pdf$/i, '')}-editable.docx`; anchor.click(); setTimeout(() => URL.revokeObjectURL(anchor.href), 3000); progress('Word 已生成', 100, '正文和公式均可在 Word 中继续编辑。'); elements.convert.disabled = false;
  }
  elements.file.addEventListener('change', async () => { const file = elements.file.files[0]; if (!file) return; state.file = file; elements.convert.disabled = true; try { await loadPdf(file); } catch (error) { console.error(error); progress('转换失败', 0, error.message || 'PDF 读取失败'); } });
  elements.preload.addEventListener('click', async () => {
    elements.preload.disabled = true; elements.file.disabled = true; elements.preload.textContent = '模型加载中...'; elements.modelStatus.textContent = '正在下载并初始化模型，请保持当前页面打开。';
    try { await loadFormulaRecognizer(); elements.preload.textContent = '模型已缓存'; elements.modelStatus.textContent = '公式模型已就绪，现在可以上传 PDF。'; progress('公式模型已就绪', 100, '模型已缓存在当前浏览器中。'); }
    catch (error) { console.error(error); elements.preload.disabled = false; elements.preload.textContent = '重新加载模型'; elements.modelStatus.textContent = '下载未完成，请检查网络后重新加载。'; progress('模型加载失败', 0, error.message || '模型下载失败'); }
    finally { elements.file.disabled = false; }
  });
  elements.quality.addEventListener('change', () => { if (state.file) loadPdf(state.file); }); elements.convert.addEventListener('click', exportDocx);
  elements.copyAll.addEventListener('click', () => navigator.clipboard.writeText(state.formulas.map((item) => item.latex).join('\n\n')));
  elements.downloadTex.addEventListener('click', () => { const blob = new Blob([state.formulas.map((item) => `\\[\n${item.latex}\n\\]`).join('\n\n')], { type: 'text/plain;charset=utf-8' }); const anchor = document.createElement('a'); anchor.href = URL.createObjectURL(blob); anchor.download = `${state.file?.name.replace(/\.pdf$/i, '') || 'formulas'}.tex`; anchor.click(); setTimeout(() => URL.revokeObjectURL(anchor.href), 2000); });
})();
</script>
