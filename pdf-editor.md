---
layout: homepage
title: PDF Editor
permalink: /pdf-editor.html
---

<div class="pdf-tool">
  <section class="pdf-tool-hero">
    <span class="pdf-tool-kicker">Local PDF Utility</span>
    <h1>PDF 文字编辑工具</h1>
    <p>在 PDF 页面上添加、移动和调整文字，然后导出新文件。所有处理均在当前浏览器中完成，文件不会上传服务器。</p>
  </section>

  <label class="pdf-upload" for="pdf-file">
    <span>
      <strong>打开一个 PDF 文件</strong>
      <span>选择本地文件后即可开始编辑</span>
    </span>
    <input id="pdf-file" type="file" accept="application/pdf,.pdf">
  </label>

  <section class="pdf-editor" id="pdf-editor" hidden>
    <div class="pdf-toolbar" aria-label="文字编辑工具栏">
      <div class="pdf-control">
        <label for="pdf-text">文字</label>
        <input id="pdf-text" type="text" value="请输入文字" maxlength="160">
      </div>
      <div class="pdf-control">
        <label for="pdf-font-size">字号</label>
        <input id="pdf-font-size" type="number" min="6" max="96" step="1" value="18">
      </div>
      <div class="pdf-control">
        <label for="pdf-color">颜色</label>
        <input id="pdf-color" type="color" value="#172033">
      </div>
      <button class="pdf-button pdf-button-primary" id="pdf-add-text" type="button">添加文字</button>
      <button class="pdf-button" id="pdf-delete-text" type="button" disabled>删除所选</button>
    </div>

    <div class="pdf-actionbar">
      <div class="pdf-action-group">
        <button class="pdf-button" id="pdf-prev" type="button">上一页</button>
        <span class="pdf-page-indicator" id="pdf-page-indicator">1 / 1</span>
        <button class="pdf-button" id="pdf-next" type="button">下一页</button>
      </div>
      <div class="pdf-action-group">
        <button class="pdf-button" id="pdf-zoom-out" type="button" aria-label="缩小">−</button>
        <span class="pdf-zoom-value" id="pdf-zoom-value">115%</span>
        <button class="pdf-button" id="pdf-zoom-in" type="button" aria-label="放大">＋</button>
        <button class="pdf-button" id="pdf-undo" type="button" disabled>撤销</button>
        <button class="pdf-button pdf-button-primary" id="pdf-export" type="button">导出 PDF</button>
      </div>
    </div>

    <div class="pdf-workspace" id="pdf-workspace">
      <div class="pdf-page-stage" id="pdf-page-stage">
        <canvas id="pdf-canvas"></canvas>
        <div class="pdf-overlay" id="pdf-overlay" aria-label="可拖动文字图层"></div>
      </div>
    </div>

    <p class="pdf-status" id="pdf-status" role="status">准备就绪。</p>
    <p class="pdf-privacy">本地处理：PDF 内容不会离开你的设备。</p>
  </section>
</div>

<script src="https://cdn.jsdelivr.net/npm/pdf-lib@1.17.1/dist/pdf-lib.min.js"></script>
<script type="module">
  import * as pdfjsLib from 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.min.mjs';

  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs';

  const elements = {
    file: document.getElementById('pdf-file'),
    editor: document.getElementById('pdf-editor'),
    canvas: document.getElementById('pdf-canvas'),
    overlay: document.getElementById('pdf-overlay'),
    stage: document.getElementById('pdf-page-stage'),
    text: document.getElementById('pdf-text'),
    size: document.getElementById('pdf-font-size'),
    color: document.getElementById('pdf-color'),
    add: document.getElementById('pdf-add-text'),
    remove: document.getElementById('pdf-delete-text'),
    prev: document.getElementById('pdf-prev'),
    next: document.getElementById('pdf-next'),
    indicator: document.getElementById('pdf-page-indicator'),
    zoomOut: document.getElementById('pdf-zoom-out'),
    zoomIn: document.getElementById('pdf-zoom-in'),
    zoomValue: document.getElementById('pdf-zoom-value'),
    undo: document.getElementById('pdf-undo'),
    export: document.getElementById('pdf-export'),
    status: document.getElementById('pdf-status')
  };

  const state = {
    bytes: null,
    fileName: 'document.pdf',
    pdf: null,
    page: 1,
    scale: 1.15,
    viewport: null,
    annotations: [],
    selectedId: null,
    history: [],
    renderTask: null,
    nextId: 1
  };

  function setStatus(message) {
    elements.status.textContent = message;
  }

  function snapshot() {
    state.history.push(JSON.stringify(state.annotations));
    if (state.history.length > 60) state.history.shift();
    elements.undo.disabled = false;
  }

  function selectAnnotation(id) {
    state.selectedId = id;
    const annotation = state.annotations.find((item) => item.id === id);
    elements.remove.disabled = !annotation;
    if (annotation) {
      elements.text.value = annotation.text;
      elements.size.value = annotation.size;
      elements.color.value = annotation.color;
    }
    renderAnnotations();
  }

  async function renderPage() {
    if (!state.pdf) return;
    if (state.renderTask) state.renderTask.cancel();
    const page = await state.pdf.getPage(state.page);
    const viewport = page.getViewport({ scale: state.scale });
    const outputScale = window.devicePixelRatio || 1;
    const context = elements.canvas.getContext('2d');

    state.viewport = viewport;
    elements.canvas.width = Math.floor(viewport.width * outputScale);
    elements.canvas.height = Math.floor(viewport.height * outputScale);
    elements.canvas.style.width = `${Math.floor(viewport.width)}px`;
    elements.canvas.style.height = `${Math.floor(viewport.height)}px`;
    elements.stage.style.width = `${Math.floor(viewport.width)}px`;
    elements.stage.style.height = `${Math.floor(viewport.height)}px`;

    const transform = outputScale === 1 ? null : [outputScale, 0, 0, outputScale, 0, 0];
    try {
      state.renderTask = page.render({ canvasContext: context, transform, viewport });
      await state.renderTask.promise;
    } catch (error) {
      if (error && error.name !== 'RenderingCancelledException') throw error;
      return;
    } finally {
      state.renderTask = null;
    }

    elements.indicator.textContent = `${state.page} / ${state.pdf.numPages}`;
    elements.zoomValue.textContent = `${Math.round(state.scale * 100)}%`;
    elements.prev.disabled = state.page <= 1;
    elements.next.disabled = state.page >= state.pdf.numPages;
    renderAnnotations();
  }

  function renderAnnotations() {
    elements.overlay.innerHTML = '';
    if (!state.viewport) return;

    state.annotations.filter((item) => item.page === state.page).forEach((annotation) => {
      const node = document.createElement('div');
      node.className = `pdf-text-item${annotation.id === state.selectedId ? ' selected' : ''}`;
      node.textContent = annotation.text;
      node.style.left = `${annotation.x * state.viewport.width}px`;
      node.style.top = `${annotation.y * state.viewport.height}px`;
      node.style.fontSize = `${annotation.size * state.scale}px`;
      node.style.color = annotation.color;
      node.dataset.id = annotation.id;
      node.addEventListener('pointerdown', startDrag);
      node.addEventListener('click', (event) => {
        event.stopPropagation();
        selectAnnotation(annotation.id);
      });
      elements.overlay.appendChild(node);
    });
  }

  function startDrag(event) {
    event.preventDefault();
    event.stopPropagation();
    const node = event.currentTarget;
    const id = Number(node.dataset.id);
    const annotation = state.annotations.find((item) => item.id === id);
    if (!annotation || !state.viewport) return;

    selectAnnotation(id);
    snapshot();
    const startX = event.clientX;
    const startY = event.clientY;
    const startLeft = parseFloat(node.style.left);
    const startTop = parseFloat(node.style.top);

    function move(moveEvent) {
      const maxLeft = Math.max(0, state.viewport.width - node.offsetWidth);
      const maxTop = Math.max(0, state.viewport.height - node.offsetHeight);
      const left = Math.min(maxLeft, Math.max(0, startLeft + moveEvent.clientX - startX));
      const top = Math.min(maxTop, Math.max(0, startTop + moveEvent.clientY - startY));
      node.style.left = `${left}px`;
      node.style.top = `${top}px`;
    }

    function end() {
      annotation.x = parseFloat(node.style.left) / state.viewport.width;
      annotation.y = parseFloat(node.style.top) / state.viewport.height;
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', end);
      setStatus('文字位置已更新。');
    }

    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', end, { once: true });
  }

  function updateSelected(property, value) {
    const annotation = state.annotations.find((item) => item.id === state.selectedId);
    if (!annotation) return;
    snapshot();
    annotation[property] = value;
    renderAnnotations();
    setStatus('所选文字已更新。');
  }

  function renderTextPng(text, size, color) {
    const ratio = 2;
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    context.font = `${size * ratio}px Arial, "Microsoft YaHei", sans-serif`;
    const width = Math.ceil(context.measureText(text).width + 8 * ratio);
    const height = Math.ceil(size * 1.45 * ratio);
    canvas.width = Math.max(width, 2);
    canvas.height = Math.max(height, 2);
    context.font = `${size * ratio}px Arial, "Microsoft YaHei", sans-serif`;
    context.fillStyle = color;
    context.textBaseline = 'top';
    context.fillText(text, 4 * ratio, 2 * ratio);
    return { dataUrl: canvas.toDataURL('image/png'), width: canvas.width / ratio, height: canvas.height / ratio };
  }

  elements.file.addEventListener('change', async () => {
    const file = elements.file.files[0];
    if (!file) return;
    try {
      setStatus('正在读取 PDF...');
      state.bytes = new Uint8Array(await file.arrayBuffer());
      state.fileName = file.name;
      state.pdf = await pdfjsLib.getDocument({ data: state.bytes.slice() }).promise;
      state.page = 1;
      state.annotations = [];
      state.selectedId = null;
      state.history = [];
      elements.undo.disabled = true;
      elements.editor.hidden = false;
      await renderPage();
      setStatus(`已打开 ${file.name}，共 ${state.pdf.numPages} 页。`);
    } catch (error) {
      setStatus('无法打开该 PDF，请确认文件没有损坏或加密。');
      console.error(error);
    }
  });

  elements.add.addEventListener('click', () => {
    if (!state.pdf || !state.viewport) return;
    const text = elements.text.value.trim();
    if (!text) {
      elements.text.focus();
      return;
    }
    snapshot();
    const annotation = {
      id: state.nextId++,
      page: state.page,
      text,
      size: Math.min(96, Math.max(6, Number(elements.size.value) || 18)),
      color: elements.color.value,
      x: 0.08,
      y: 0.1
    };
    state.annotations.push(annotation);
    selectAnnotation(annotation.id);
    setStatus('文字已添加，可直接拖动调整位置。');
  });

  elements.remove.addEventListener('click', () => {
    if (!state.selectedId) return;
    snapshot();
    state.annotations = state.annotations.filter((item) => item.id !== state.selectedId);
    state.selectedId = null;
    elements.remove.disabled = true;
    renderAnnotations();
    setStatus('所选文字已删除。');
  });

  elements.text.addEventListener('change', () => updateSelected('text', elements.text.value.trim() || '文字'));
  elements.size.addEventListener('change', () => updateSelected('size', Math.min(96, Math.max(6, Number(elements.size.value) || 18))));
  elements.color.addEventListener('change', () => updateSelected('color', elements.color.value));
  elements.overlay.addEventListener('click', () => selectAnnotation(null));

  elements.prev.addEventListener('click', async () => {
    if (state.page > 1) {
      state.page--;
      selectAnnotation(null);
      await renderPage();
    }
  });

  elements.next.addEventListener('click', async () => {
    if (state.pdf && state.page < state.pdf.numPages) {
      state.page++;
      selectAnnotation(null);
      await renderPage();
    }
  });

  elements.zoomOut.addEventListener('click', async () => {
    state.scale = Math.max(0.6, Number((state.scale - 0.15).toFixed(2)));
    await renderPage();
  });

  elements.zoomIn.addEventListener('click', async () => {
    state.scale = Math.min(2.2, Number((state.scale + 0.15).toFixed(2)));
    await renderPage();
  });

  elements.undo.addEventListener('click', () => {
    if (!state.history.length) return;
    state.annotations = JSON.parse(state.history.pop());
    state.selectedId = null;
    elements.remove.disabled = true;
    elements.undo.disabled = state.history.length === 0;
    renderAnnotations();
    setStatus('已撤销上一步操作。');
  });

  elements.export.addEventListener('click', async () => {
    if (!state.bytes) return;
    const originalLabel = elements.export.textContent;
    try {
      elements.export.disabled = true;
      elements.export.textContent = '正在导出...';
      setStatus('正在生成新 PDF...');
      const pdfDocument = await window.PDFLib.PDFDocument.load(state.bytes.slice());
      const pages = pdfDocument.getPages();

      for (const annotation of state.annotations) {
        const page = pages[annotation.page - 1];
        if (!page) continue;
        const rendered = renderTextPng(annotation.text, annotation.size, annotation.color);
        const image = await pdfDocument.embedPng(rendered.dataUrl);
        const pageSize = page.getSize();
        page.drawImage(image, {
          x: annotation.x * pageSize.width,
          y: pageSize.height - annotation.y * pageSize.height - rendered.height,
          width: rendered.width,
          height: rendered.height
        });
      }

      const saved = await pdfDocument.save();
      const blob = new Blob([saved], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = state.fileName.replace(/\.pdf$/i, '') + '-edited.pdf';
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setStatus('导出完成，文件已保存到下载目录。');
    } catch (error) {
      setStatus('导出失败，请重新打开文件后再试。');
      console.error(error);
    } finally {
      elements.export.disabled = false;
      elements.export.textContent = originalLabel;
    }
  });

  window.addEventListener('keydown', (event) => {
    const editingInput = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName);
    if ((event.key === 'Delete' || event.key === 'Backspace') && state.selectedId && !editingInput) {
      event.preventDefault();
      elements.remove.click();
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z' && !editingInput) {
      event.preventDefault();
      elements.undo.click();
    }
  });
</script>
