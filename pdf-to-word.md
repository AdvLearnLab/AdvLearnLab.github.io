---
layout: homepage
title: PDF 转 Word
permalink: /pdf-to-word.html
---

<script src="https://cdn.jsdelivr.net/npm/docx@8.5.0/build/index.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>

<div class="pdf-word-tool">
  <header class="pdf-word-hero">
    <span>PDF Conversion</span>
    <h1>PDF 转 Word</h1>
    <p>转换在浏览器本地完成。高保真模式保持原页面和公式外观；公式 LaTeX 会显示在右侧。</p>
  </header>

  <label class="pdf-word-upload">
    <span><strong>选择 PDF 文件</strong><span>文件不会上传服务器，支持文字型与扫描型 PDF。</span></span>
    <input id="pdf-word-file" type="file" accept="application/pdf,.pdf">
  </label>

  <div class="pdf-word-options">
    <div class="pdf-word-field"><label for="pdf-word-mode">转换模式</label><select id="pdf-word-mode"><option value="fidelity">高保真模式（推荐，无乱码）</option><option value="editable">可编辑文字模式</option></select></div>
    <div class="pdf-word-field"><label for="pdf-word-quality">页面清晰度</label><select id="pdf-word-quality"><option value="1.5">标准</option><option value="2" selected>高清</option><option value="2.5">超清</option></select></div>
    <button id="pdf-word-convert" class="pdf-word-button" type="button" disabled>转换并下载 Word</button>
  </div>

  <div id="pdf-word-progress" class="pdf-word-progress" hidden>
    <div class="pdf-word-progress-head"><strong id="pdf-word-progress-title">准备转换</strong><span id="pdf-word-progress-value">0%</span></div>
    <div class="pdf-word-track"><span id="pdf-word-progress-bar"></span></div>
  </div>

  <div id="pdf-word-workspace" class="pdf-word-workspace" hidden>
    <section class="pdf-word-panel"><h2>页面预览</h2><div id="pdf-word-pages" class="pdf-word-pages"></div></section>
    <aside class="pdf-word-panel"><h2>公式 LaTeX</h2><div id="pdf-word-formulas" class="pdf-word-formulas"><div class="pdf-word-empty">正在分析 PDF 公式...</div></div><div class="pdf-word-side-actions"><button id="pdf-word-copy-all" class="pdf-word-button" type="button">复制全部</button><button id="pdf-word-download-tex" class="pdf-word-button" type="button">下载 .tex</button></div></aside>
  </div>
</div>

<script type="module">
(() => {
  const state = { file: null, pdf: null, pages: [], formulas: [] };
  const elements = {
    file: document.querySelector('#pdf-word-file'), mode: document.querySelector('#pdf-word-mode'), quality: document.querySelector('#pdf-word-quality'),
    convert: document.querySelector('#pdf-word-convert'), progress: document.querySelector('#pdf-word-progress'), progressTitle: document.querySelector('#pdf-word-progress-title'),
    progressValue: document.querySelector('#pdf-word-progress-value'), progressBar: document.querySelector('#pdf-word-progress-bar'), workspace: document.querySelector('#pdf-word-workspace'),
    pages: document.querySelector('#pdf-word-pages'), formulas: document.querySelector('#pdf-word-formulas'), copyAll: document.querySelector('#pdf-word-copy-all'), downloadTex: document.querySelector('#pdf-word-download-tex')
  };
  let pdfjsPromise;

  async function getPdfJs() {
    if (!pdfjsPromise) pdfjsPromise = import('https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.min.mjs').then((pdfjs) => {
      pdfjs.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs';
      return pdfjs;
    });
    return pdfjsPromise;
  }

  function progress(title, value) {
    elements.progress.hidden = false;
    elements.progressTitle.textContent = title;
    elements.progressValue.textContent = `${Math.round(value)}%`;
    elements.progressBar.style.width = `${Math.max(0, Math.min(100, value))}%`;
  }

  function normalizeLatex(text) {
    return text.trim().replace(/≤/g, '\\leq ').replace(/≥/g, '\\geq ').replace(/≠/g, '\\neq ').replace(/≈/g, '\\approx ')
      .replace(/×/g, '\\times ').replace(/÷/g, '\\div ').replace(/±/g, '\\pm ').replace(/√\s*([A-Za-z0-9]+)/g, '\\sqrt{$1}')
      .replace(/∑/g, '\\sum ').replace(/∏/g, '\\prod ').replace(/∫/g, '\\int ').replace(/∞/g, '\\infty ')
      .replace(/α/g, '\\alpha ').replace(/β/g, '\\beta ').replace(/γ/g, '\\gamma ').replace(/δ/g, '\\delta ').replace(/λ/g, '\\lambda ')
      .replace(/([A-Za-z0-9])²/g, '$1^{2}').replace(/([A-Za-z0-9])³/g, '$1^{3}');
  }

  function looksLikeFormula(text) {
    const value = text.trim();
    if (value.length < 2 || value.length > 300) return false;
    const operators = (value.match(/[=<>≤≥≠≈∑∏∫√±×÷^_{}()[\]]/g) || []).length;
    const symbols = (value.match(/[α-ωΑ-Ω]/g) || []).length;
    const digits = (value.match(/\d/g) || []).length;
    return operators + symbols >= 1 && operators + symbols + digits >= 2;
  }

  function groupText(items) {
    const rows = [];
    items.forEach((item) => {
      const y = Math.round(item.transform[5]);
      let row = rows.find((candidate) => Math.abs(candidate.y - y) <= 3);
      if (!row) { row = { y, items: [] }; rows.push(row); }
      row.items.push(item);
    });
    return rows.sort((a, b) => b.y - a.y).map((row) => row.items.sort((a, b) => a.transform[4] - b.transform[4]).map((item) => item.str).join(' ').replace(/\s+/g, ' ').trim()).filter(Boolean);
  }

  function addFormula(latex, pageNumber) {
    const value = normalizeLatex(latex).replace(/^\$+|\$+$/g, '').trim();
    if (!value || state.formulas.some((item) => item.latex === value)) return;
    state.formulas.push({ latex: value, pageNumber });
  }

  function renderFormulas() {
    if (!state.formulas.length) { elements.formulas.innerHTML = '<div class="pdf-word-empty">未在文字层发现明确公式。扫描版 PDF 的公式会原样保留在高保真 Word 页面中。</div>'; return; }
    elements.formulas.innerHTML = '';
    state.formulas.forEach((item, index) => {
      const card = document.createElement('div'); card.className = 'pdf-word-formula';
      card.innerHTML = `<div class="pdf-word-formula-head"><span>第 ${item.pageNumber} 页 · 公式 ${index + 1}</span><button class="pdf-word-copy" type="button">复制</button></div><textarea class="pdf-word-latex"></textarea><div class="pdf-word-preview"></div>`;
      const textarea = card.querySelector('textarea'); const preview = card.querySelector('.pdf-word-preview'); textarea.value = item.latex;
      const draw = () => { item.latex = textarea.value; try { katex.render(item.latex, preview, { throwOnError: false, displayMode: true }); } catch (_) { preview.textContent = item.latex; } };
      textarea.addEventListener('input', draw); card.querySelector('button').addEventListener('click', async () => { await navigator.clipboard.writeText(textarea.value); }); draw(); elements.formulas.appendChild(card);
    });
  }

  async function loadPdf(file) {
    progress('读取 PDF', 4);
    const pdfjs = await getPdfJs();
    state.pdf = await pdfjs.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise;
    state.pages = []; state.formulas = []; elements.pages.innerHTML = ''; elements.workspace.hidden = false;
    const scale = Number(elements.quality.value);
    for (let number = 1; number <= state.pdf.numPages; number++) {
      progress(`解析第 ${number} / ${state.pdf.numPages} 页`, 8 + number / state.pdf.numPages * 65);
      const page = await state.pdf.getPage(number); const viewport = page.getViewport({ scale });
      const canvas = document.createElement('canvas'); canvas.width = Math.ceil(viewport.width); canvas.height = Math.ceil(viewport.height);
      await page.render({ canvasContext: canvas.getContext('2d', { alpha: false }), viewport }).promise;
      elements.pages.appendChild(canvas);
      const text = await page.getTextContent(); const lines = groupText(text.items); lines.filter(looksLikeFormula).forEach((line) => addFormula(line, number));
      state.pages.push({ canvas, lines, width: viewport.width, height: viewport.height });
    }
    renderFormulas(); progress('PDF 已准备', 100); elements.convert.disabled = false;
  }

  const canvasBytes = (canvas) => new Promise((resolve) => canvas.toBlob(async (blob) => resolve(new Uint8Array(await blob.arrayBuffer())), 'image/png'));

  async function exportDocx() {
    if (!state.pages.length || !window.docx) return;
    elements.convert.disabled = true; progress('生成 Word', 5);
    const { Document, Packer, Paragraph, ImageRun, PageBreak, TextRun, AlignmentType } = window.docx;
    const children = [];
    if (elements.mode.value === 'fidelity') {
      for (let index = 0; index < state.pages.length; index++) {
        const page = state.pages[index]; const ratio = Math.min(720 / page.width, 1000 / page.height); const data = await canvasBytes(page.canvas);
        children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ data, transformation: { width: Math.round(page.width * ratio), height: Math.round(page.height * ratio) } })] }));
        if (index < state.pages.length - 1) children.push(new Paragraph({ children: [new PageBreak()] }));
        progress(`写入第 ${index + 1} / ${state.pages.length} 页`, 10 + (index + 1) / state.pages.length * 75);
      }
    } else {
      state.pages.forEach((page, pageIndex) => {
        page.lines.forEach((line) => children.push(new Paragraph({ children: [new TextRun({ text: line, font: 'Microsoft YaHei', size: 22 })], spacing: { after: 100 } })));
        if (pageIndex < state.pages.length - 1) children.push(new Paragraph({ children: [new PageBreak()] }));
      });
    }
    const doc = new Document({ sections: [{ properties: { page: { margin: { top: 360, right: 360, bottom: 360, left: 360 } } }, children }] });
    const blob = await Packer.toBlob(doc);
    const anchor = window.document.createElement('a'); anchor.href = URL.createObjectURL(blob); anchor.download = `${state.file.name.replace(/\.pdf$/i, '')}.docx`; anchor.click(); setTimeout(() => URL.revokeObjectURL(anchor.href), 2000);
    progress('Word 已生成', 100); elements.convert.disabled = false;
  }

  elements.file.addEventListener('change', async () => { const file = elements.file.files[0]; if (!file) return; state.file = file; elements.convert.disabled = true; try { await loadPdf(file); } catch (error) { console.error(error); progress('PDF 读取失败', 0); } });
  elements.quality.addEventListener('change', () => { if (state.file) loadPdf(state.file); });
  elements.convert.addEventListener('click', exportDocx);
  elements.copyAll.addEventListener('click', () => navigator.clipboard.writeText(state.formulas.map((item) => item.latex).join('\n\n')));
  elements.downloadTex.addEventListener('click', () => { const blob = new Blob([state.formulas.map((item) => `\\[\n${item.latex}\n\\]`).join('\n\n')], { type: 'text/plain;charset=utf-8' }); const anchor = document.createElement('a'); anchor.href = URL.createObjectURL(blob); anchor.download = `${state.file?.name.replace(/\.pdf$/i, '') || 'formulas'}.tex`; anchor.click(); setTimeout(() => URL.revokeObjectURL(anchor.href), 2000); });
})();
</script>
