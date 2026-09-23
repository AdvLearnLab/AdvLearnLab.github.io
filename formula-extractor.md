---
layout: homepage
title: Formula to LaTeX
permalink: /formula-extractor.html
---

<div class="formula-tool">
  <div class="formula-hero">
    <span>Local Formula Utility</span>
    <h1>文档公式转 LaTeX</h1>
    <p>上传 Word、PDF 或公式截图，提取并预览 LaTeX。文档在浏览器本地解析；图像识别模型首次使用时会下载并缓存在浏览器中。</p>
  </div>

  <label class="formula-upload" for="formula-file">
    <span><strong>上传文档或公式图片</strong><span>支持 DOCX、PDF、PNG、JPEG、WebP、BMP；旧版 DOC 请先另存为 DOCX</span></span>
    <input id="formula-file" type="file" accept=".docx,.pdf,image/png,image/jpeg,image/webp,image/bmp">
  </label>

  <div class="formula-source" id="formula-source" hidden>
    <div>
      <strong id="formula-file-name">尚未选择文件</strong>
      <span id="formula-file-meta"></span>
    </div>
    <button class="formula-button formula-button-primary" id="formula-extract" type="button">开始提取</button>
  </div>

  <div class="formula-preview" id="formula-preview" hidden>
    <img id="formula-image-preview" alt="待识别公式预览">
  </div>

  <div class="formula-progress" id="formula-progress" hidden>
    <div><strong id="formula-progress-title">正在准备</strong><span id="formula-progress-value">0%</span></div>
    <progress id="formula-progress-bar" max="100" value="0"></progress>
    <p id="formula-status" role="status">准备就绪。</p>
  </div>

  <section class="formula-results" id="formula-results" hidden>
    <div class="formula-results-head">
      <div><span>Extraction Results</span><h2>识别结果 <small id="formula-count">0</small></h2></div>
      <div class="formula-result-actions">
        <button class="formula-button" id="formula-copy-all" type="button">复制全部</button>
        <button class="formula-button" id="formula-download" type="button">下载 .tex</button>
      </div>
    </div>
    <div id="formula-list"></div>
  </section>

  <div class="formula-empty" id="formula-empty">
    <strong>适合处理</strong>
    <span>Word 原生公式、论文 PDF 中的独立公式行，以及裁剪清晰的公式截图。</span>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script type="module">
  import * as pdfjsLib from 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.min.mjs';
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs';

  const elements = {
    file: document.getElementById('formula-file'),
    source: document.getElementById('formula-source'),
    fileName: document.getElementById('formula-file-name'),
    fileMeta: document.getElementById('formula-file-meta'),
    extract: document.getElementById('formula-extract'),
    preview: document.getElementById('formula-preview'),
    imagePreview: document.getElementById('formula-image-preview'),
    progress: document.getElementById('formula-progress'),
    progressTitle: document.getElementById('formula-progress-title'),
    progressValue: document.getElementById('formula-progress-value'),
    progressBar: document.getElementById('formula-progress-bar'),
    status: document.getElementById('formula-status'),
    results: document.getElementById('formula-results'),
    count: document.getElementById('formula-count'),
    list: document.getElementById('formula-list'),
    copyAll: document.getElementById('formula-copy-all'),
    download: document.getElementById('formula-download'),
    empty: document.getElementById('formula-empty')
  };

  const state = { file: null, objectUrl: null, formulas: [], recognizer: null };
  const imageTypes = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/bmp']);

  const symbolMap = {
    '−': '-', '×': '\\times ', '÷': '\\div ', '±': '\\pm ', '∓': '\\mp ',
    '≤': '\\le ', '≥': '\\ge ', '≠': '\\ne ', '≈': '\\approx ', '∞': '\\infty ',
    '→': '\\to ', '←': '\\leftarrow ', '↔': '\\leftrightarrow ', '∈': '\\in ', '∉': '\\notin ',
    '∂': '\\partial ', '∇': '\\nabla ', '∑': '\\sum ', '∏': '\\prod ', '∫': '\\int ',
    'α': '\\alpha ', 'β': '\\beta ', 'γ': '\\gamma ', 'δ': '\\delta ', 'ε': '\\epsilon ',
    'θ': '\\theta ', 'λ': '\\lambda ', 'μ': '\\mu ', 'π': '\\pi ', 'ρ': '\\rho ',
    'σ': '\\sigma ', 'τ': '\\tau ', 'φ': '\\phi ', 'ω': '\\omega ', 'Δ': '\\Delta ',
    'Γ': '\\Gamma ', 'Λ': '\\Lambda ', 'Σ': '\\Sigma ', 'Φ': '\\Phi ', 'Ω': '\\Omega '
  };

  function localName(node) { return node?.localName || node?.nodeName?.split(':').pop() || ''; }
  function children(node, name) { return Array.from(node?.children || []).filter((child) => !name || localName(child) === name); }
  function first(node, name) { return children(node, name)[0] || null; }
  function attr(node, name, fallback = '') {
    if (!node) return fallback;
    return node.getAttribute(`m:${name}`) || node.getAttribute(name) || Array.from(node.attributes || []).find((item) => item.localName === name)?.value || fallback;
  }
  function braces(value) { return `{${value || ''}}`; }
  function normalizeSymbols(value) { return Array.from(value || '').map((char) => symbolMap[char] || char).join(''); }

  function ommlToLatex(node) {
    if (!node) return '';
    const name = localName(node);
    if (name === 't') return normalizeSymbols(node.textContent);
    if (name === 'f') return `\\frac${braces(ommlToLatex(first(node, 'num')))}${braces(ommlToLatex(first(node, 'den')))}`;
    if (name === 'sSup') return `${ommlToLatex(first(node, 'e'))}^${braces(ommlToLatex(first(node, 'sup')))}`;
    if (name === 'sSub') return `${ommlToLatex(first(node, 'e'))}_${braces(ommlToLatex(first(node, 'sub')))}`;
    if (name === 'sSubSup') return `${ommlToLatex(first(node, 'e'))}_${braces(ommlToLatex(first(node, 'sub')))}^${braces(ommlToLatex(first(node, 'sup')))}`;
    if (name === 'rad') {
      const degree = ommlToLatex(first(node, 'deg'));
      return degree ? `\\sqrt[${degree}]${braces(ommlToLatex(first(node, 'e')))}` : `\\sqrt${braces(ommlToLatex(first(node, 'e')))}`;
    }
    if (name === 'nary') {
      const properties = first(node, 'naryPr');
      const character = attr(first(properties, 'chr'), 'val', '∫');
      const operator = symbolMap[character]?.trim() || normalizeSymbols(character);
      const lower = ommlToLatex(first(node, 'sub'));
      const upper = ommlToLatex(first(node, 'sup'));
      return `${operator}${lower ? `_${braces(lower)}` : ''}${upper ? `^${braces(upper)}` : ''} ${ommlToLatex(first(node, 'e'))}`;
    }
    if (name === 'd') {
      const properties = first(node, 'dPr');
      const begin = attr(first(properties, 'begChr'), 'val', '(');
      const end = attr(first(properties, 'endChr'), 'val', ')');
      return `\\left${begin}${ommlToLatex(first(node, 'e'))}\\right${end}`;
    }
    if (name === 'm') {
      const rows = children(node, 'mr').map((row) => children(row, 'e').map(ommlToLatex).join(' & '));
      return `\\begin{matrix}${rows.join(' \\\\ ')}\\end{matrix}`;
    }
    if (name === 'eqArr') return children(node, 'e').map(ommlToLatex).join(' \\\\ ');
    if (name === 'func') return `${ommlToLatex(first(node, 'fName'))}\\left(${ommlToLatex(first(node, 'e'))}\\right)`;
    if (name === 'acc') {
      const character = attr(first(first(node, 'accPr'), 'chr'), 'val', '̂');
      const command = character === '̇' ? '\\dot' : character === '̈' ? '\\ddot' : character === '⃗' ? '\\vec' : '\\hat';
      return `${command}${braces(ommlToLatex(first(node, 'e')))}`;
    }
    if (name === 'bar') {
      const position = attr(first(first(node, 'barPr'), 'pos'), 'val', 'top');
      return `${position === 'bot' ? '\\underline' : '\\overline'}${braces(ommlToLatex(first(node, 'e')))}`;
    }
    if (name === 'limLow') return `${ommlToLatex(first(node, 'e'))}_${braces(ommlToLatex(first(node, 'lim')))}`;
    if (name === 'limUpp') return `${ommlToLatex(first(node, 'e'))}^${braces(ommlToLatex(first(node, 'lim')))}`;
    return children(node).filter((child) => !localName(child).endsWith('Pr')).map(ommlToLatex).join('');
  }

  function cleanLatex(value) {
    return (value || '').replace(/^\s*\$+|\$+\s*$/g, '').replace(/^\\\[|\\\]$/g, '').replace(/\s+/g, ' ').trim();
  }

  function setProgress(title, percent, status) {
    elements.progress.hidden = false;
    elements.progressTitle.textContent = title;
    const safe = Math.max(0, Math.min(100, Math.round(percent || 0)));
    elements.progressValue.textContent = `${safe}%`;
    elements.progressBar.value = safe;
    if (status) elements.status.textContent = status;
  }

  async function copyText(value) {
    try {
      await navigator.clipboard.writeText(value);
    } catch (_) {
      const area = document.createElement('textarea');
      area.value = value;
      document.body.appendChild(area);
      area.select();
      document.execCommand('copy');
      area.remove();
    }
  }

  function addFormula(latex, source) {
    const normalized = cleanLatex(latex);
    if (!normalized || state.formulas.some((item) => item.latex === normalized)) return;
    state.formulas.push({ latex: normalized, source });
  }

  function renderResults() {
    elements.list.innerHTML = '';
    elements.results.hidden = state.formulas.length === 0;
    elements.empty.hidden = state.formulas.length > 0;
    elements.count.textContent = state.formulas.length;
    state.formulas.forEach((formula, index) => {
      const card = document.createElement('article');
      card.className = 'formula-card';
      const top = document.createElement('div');
      top.className = 'formula-card-top';
      top.innerHTML = `<span>公式 ${index + 1}</span><small>${formula.source}</small>`;
      const preview = document.createElement('div');
      preview.className = 'formula-render';
      const editor = document.createElement('textarea');
      editor.className = 'formula-code';
      editor.value = formula.latex;
      editor.rows = 3;
      const copy = document.createElement('button');
      copy.className = 'formula-button formula-copy';
      copy.type = 'button';
      copy.textContent = '复制 LaTeX';
      const draw = () => {
        formula.latex = editor.value;
        try { window.katex.render(formula.latex, preview, { throwOnError: false, displayMode: true }); }
        catch (_) { preview.textContent = formula.latex; }
      };
      editor.addEventListener('input', draw);
      copy.addEventListener('click', async () => {
        await copyText(editor.value);
        copy.textContent = '已复制';
        setTimeout(() => { copy.textContent = '复制 LaTeX'; }, 1200);
      });
      card.append(top, preview, editor, copy);
      elements.list.appendChild(card);
      draw();
    });
  }

  async function extractDocx(file) {
    setProgress('解析 Word 公式', 12, '正在读取 DOCX 文档结构...');
    const zip = await window.JSZip.loadAsync(await file.arrayBuffer());
    const entry = zip.file('word/document.xml');
    if (!entry) throw new Error('DOCX 中缺少 document.xml');
    const xml = new DOMParser().parseFromString(await entry.async('text'), 'application/xml');
    const equations = Array.from(xml.getElementsByTagNameNS('*', 'oMath')).filter((node) => localName(node.parentElement) !== 'oMath');
    equations.forEach((node, index) => addFormula(ommlToLatex(node), `Word 原生公式 ${index + 1}`));
    setProgress('解析 Word 公式', 100, `已找到 ${state.formulas.length} 条原生公式。`);
  }

  function looksMathematical(text) {
    const value = text.trim();
    if (value.length < 2 || value.length > 360) return false;
    const operators = (value.match(/[=<>≤≥≠≈∑∏∫√±×÷^_{}()[\]]/g) || []).length;
    const greek = (value.match(/[α-ωΑ-Ω]/g) || []).length;
    const digits = (value.match(/\d/g) || []).length;
    const words = (value.match(/[A-Za-z]{4,}/g) || []).length;
    return operators + greek >= 1 && (operators + greek + digits >= 2 || words === 0);
  }

  function plainMathToLatex(text) {
    return normalizeSymbols(text).replace(/([A-Za-z0-9)])²/g, '$1^{2}').replace(/([A-Za-z0-9)])³/g, '$1^{3}');
  }

  async function loadRecognizer() {
    if (state.recognizer) return state.recognizer;
    setProgress('加载公式识别模型', 2, '首次使用需下载浏览器模型，请保持页面打开...');
    const { pipeline, env } = await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.2/+esm');
    env.allowLocalModels = false;
    state.recognizer = await pipeline('image-to-text', 'Ji-Ha/TexTeller3-ONNX-dynamic', {
      device: navigator.gpu ? 'webgpu' : 'wasm',
      progress_callback: (progress) => {
        const percent = progress.progress || (progress.loaded && progress.total ? progress.loaded / progress.total * 100 : 4);
        setProgress('加载公式识别模型', percent, progress.file ? `正在加载 ${progress.file}` : '正在准备模型...');
      }
    });
    return state.recognizer;
  }

  async function recognizeImage(source, label) {
    const recognizer = await loadRecognizer();
    setProgress('识别公式', 75, `正在识别 ${label}...`);
    const output = await recognizer(source, { max_new_tokens: 256 });
    const latex = output?.[0]?.generated_text || output?.generated_text || '';
    addFormula(latex, label);
  }

  async function imageFromFile(file) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      const url = URL.createObjectURL(file);
      image.onload = () => { URL.revokeObjectURL(url); resolve(image); };
      image.onerror = () => { URL.revokeObjectURL(url); reject(new Error('图片读取失败')); };
      image.src = url;
    });
  }

  async function extractPdf(file) {
    setProgress('分析 PDF', 8, '正在读取 PDF 文本层并定位公式...');
    const pdfDocument = await pdfjsLib.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise;
    const crops = [];
    for (let pageNumber = 1; pageNumber <= pdfDocument.numPages; pageNumber++) {
      const page = await pdfDocument.getPage(pageNumber);
      const viewport = page.getViewport({ scale: 2 });
      const text = await page.getTextContent();
      const lines = new Map();
      text.items.forEach((item) => {
        const point = pdfjsLib.Util.transform(viewport.transform, item.transform);
        const key = Math.round(point[5] / 7) * 7;
        const current = lines.get(key) || [];
        current.push({ text: item.str, x: point[4], y: point[5], width: item.width * 2, height: Math.max(12, Math.hypot(point[2], point[3])) });
        lines.set(key, current);
      });
      const candidates = Array.from(lines.values()).map((items) => {
        items.sort((a, b) => a.x - b.x);
        return { items, text: items.map((item) => item.text).join(' ').trim() };
      }).filter((line) => looksMathematical(line.text));

      if (!candidates.length) continue;
      const canvas = document.createElement('canvas');
      canvas.width = Math.ceil(viewport.width);
      canvas.height = Math.ceil(viewport.height);
      await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;
      for (const candidate of candidates.slice(0, 30 - crops.length)) {
        addFormula(plainMathToLatex(candidate.text), `PDF 第 ${pageNumber} 页文本候选`);
        const minX = Math.max(0, Math.min(...candidate.items.map((item) => item.x)) - 18);
        const maxX = Math.min(canvas.width, Math.max(...candidate.items.map((item) => item.x + item.width)) + 18);
        const baseline = candidate.items[0].y;
        const lineHeight = Math.max(...candidate.items.map((item) => item.height));
        const minY = Math.max(0, baseline - lineHeight * 1.5 - 10);
        const maxY = Math.min(canvas.height, baseline + lineHeight * 0.5 + 10);
        const crop = document.createElement('canvas');
        crop.width = Math.max(2, Math.round(maxX - minX));
        crop.height = Math.max(2, Math.round(maxY - minY));
        crop.getContext('2d').drawImage(canvas, minX, minY, crop.width, crop.height, 0, 0, crop.width, crop.height);
        crops.push({ canvas: crop, label: `PDF 第 ${pageNumber} 页公式区域` });
      }
      setProgress('分析 PDF', 10 + pageNumber / pdfDocument.numPages * 35, `已分析 ${pageNumber} / ${pdfDocument.numPages} 页`);
      if (crops.length >= 30) break;
    }

    if (crops.length) {
      for (let index = 0; index < crops.length; index++) {
        setProgress('识别 PDF 公式', 48 + index / crops.length * 48, `正在识别 ${index + 1} / ${crops.length} 个公式区域`);
        try { await recognizeImage(crops[index].canvas, crops[index].label); } catch (error) { console.warn(error); }
      }
    }
    setProgress('PDF 公式提取完成', 100, state.formulas.length ? `共整理 ${state.formulas.length} 条公式候选。` : '没有定位到公式；扫描版 PDF 请截取公式区域后以图片上传。');
  }

  elements.file.addEventListener('change', () => {
    const file = elements.file.files[0];
    if (!file) return;
    state.file = file;
    state.formulas = [];
    if (state.objectUrl) URL.revokeObjectURL(state.objectUrl);
    elements.fileName.textContent = file.name;
    elements.fileMeta.textContent = `${Math.max(1, Math.round(file.size / 1024))} KB · ${file.type || 'document'}`;
    elements.source.hidden = false;
    elements.results.hidden = true;
    elements.empty.hidden = false;
    elements.progress.hidden = true;
    elements.preview.hidden = !imageTypes.has(file.type);
    if (imageTypes.has(file.type)) {
      state.objectUrl = URL.createObjectURL(file);
      elements.imagePreview.src = state.objectUrl;
    }
  });

  elements.extract.addEventListener('click', async () => {
    if (!state.file) return;
    state.formulas = [];
    elements.extract.disabled = true;
    elements.extract.textContent = '正在处理...';
    try {
      const name = state.file.name.toLowerCase();
      if (name.endsWith('.docx')) await extractDocx(state.file);
      else if (name.endsWith('.pdf')) await extractPdf(state.file);
      else if (imageTypes.has(state.file.type)) {
        const image = await imageFromFile(state.file);
        await recognizeImage(image, '公式截图');
        setProgress('图片公式识别完成', 100, state.formulas.length ? '识别完成，可检查并编辑结果。' : '未识别到公式，请裁剪出更清晰的公式区域后重试。');
      } else throw new Error('暂不支持该文件格式');
      renderResults();
    } catch (error) {
      console.error(error);
      setProgress('处理失败', 0, `无法完成提取：${error.message || '请检查文件后重试'}`);
      renderResults();
    } finally {
      elements.extract.disabled = false;
      elements.extract.textContent = '重新提取';
    }
  });

  elements.copyAll.addEventListener('click', async () => {
    await copyText(state.formulas.map((item) => `\\[\n${item.latex}\n\\]`).join('\n\n'));
    elements.copyAll.textContent = '已复制全部';
    setTimeout(() => { elements.copyAll.textContent = '复制全部'; }, 1200);
  });

  elements.download.addEventListener('click', () => {
    const body = state.formulas.map((item) => `\\[\n${item.latex}\n\\]`).join('\n\n');
    const blob = new Blob([body], { type: 'text/x-tex;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${state.file?.name.replace(/\.[^.]+$/, '') || 'formulas'}-formulas.tex`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
</script>
