---
layout: homepage
title: Image Editor
permalink: /image-editor.html
---

<div class="image-tool">
  <div class="image-tool-hero">
    <span>Local Image Utility</span>
    <h1>图像编辑工具</h1>
    <p>上传图片后进行缩放、旋转、翻转和色彩调整，再导出为常用图像格式。所有处理都在浏览器本地完成。</p>
  </div>

  <label class="image-upload" for="image-file">
    <span>
      <strong>打开一张图片</strong>
      <span>支持 PNG、JPEG、WebP、BMP 和 GIF 静态帧</span>
    </span>
    <input id="image-file" type="file" accept="image/png,image/jpeg,image/webp,image/bmp,image/gif">
  </label>

  <section class="image-editor" id="image-editor" hidden>
    <div class="image-resize-panel">
      <div class="image-resize-heading">
        <strong>输出尺寸</strong>
        <span>精确控制导出图片的像素大小</span>
      </div>
      <div class="image-dimension-field">
        <label for="image-width">宽度 A</label>
        <div><input id="image-width" type="number" min="1" max="12000" step="1"><span>px</span></div>
      </div>
      <span class="image-dimension-times" aria-hidden="true">×</span>
      <div class="image-dimension-field">
        <label for="image-height">高度 B</label>
        <div><input id="image-height" type="number" min="1" max="12000" step="1"><span>px</span></div>
      </div>
      <label class="image-ratio-lock"><input id="image-ratio-lock" type="checkbox" checked> 锁定比例</label>
      <select class="image-select" id="image-fit-mode" aria-label="图片适配方式">
        <option value="cover">填满并居中裁切</option>
        <option value="contain">完整显示并留白</option>
        <option value="stretch">拉伸到指定尺寸</option>
      </select>
      <button class="image-button image-button-primary" id="image-apply-size" type="button">应用尺寸</button>
    </div>

    <div class="image-presets">
      <label for="image-size-preset">常用证件照</label>
      <select class="image-select" id="image-size-preset">
        <option value="">选择尺寸</option>
        <option value="260x378">小一寸 · 260 × 378 px</option>
        <option value="295x413">一寸 · 295 × 413 px</option>
        <option value="390x567">大一寸 / 护照常用 · 390 × 567 px</option>
        <option value="413x531">小二寸 · 413 × 531 px</option>
        <option value="413x579">二寸 · 413 × 579 px</option>
        <option value="413x626">大二寸 · 413 × 626 px</option>
        <option value="358x441">居民身份证常用 · 358 × 441 px</option>
      </select>
      <span>不同报名系统要求可能不同，请以具体通知为准。</span>
    </div>

    <div class="image-toolbar">
      <div class="image-control">
        <label for="image-brightness"><span>亮度</span><output id="brightness-value">100%</output></label>
        <input id="image-brightness" type="range" min="0" max="200" value="100">
      </div>
      <div class="image-control">
        <label for="image-contrast"><span>对比度</span><output id="contrast-value">100%</output></label>
        <input id="image-contrast" type="range" min="0" max="200" value="100">
      </div>
      <div class="image-control">
        <label for="image-saturation"><span>饱和度</span><output id="saturation-value">100%</output></label>
        <input id="image-saturation" type="range" min="0" max="200" value="100">
      </div>
    </div>

    <div class="image-actions">
      <div class="image-action-group">
        <button class="image-button" id="rotate-left" type="button">左转 90°</button>
        <button class="image-button" id="rotate-right" type="button">右转 90°</button>
        <button class="image-button" id="flip-horizontal" type="button">水平翻转</button>
        <button class="image-button" id="flip-vertical" type="button">垂直翻转</button>
        <button class="image-button" id="toggle-grayscale" type="button">灰度</button>
        <button class="image-button" id="auto-enhance" type="button">自动增强</button>
      </div>
      <div class="image-action-group">
        <button class="image-button" id="zoom-out" type="button" aria-label="缩小">−</button>
        <span class="image-zoom-label" id="zoom-label">100%</span>
        <button class="image-button" id="zoom-in" type="button" aria-label="放大">＋</button>
        <button class="image-button" id="image-undo" type="button" disabled>撤销</button>
        <button class="image-button" id="image-reset" type="button">重置</button>
      </div>
    </div>

    <div class="image-workspace" id="image-workspace">
      <div class="image-stage"><canvas id="image-canvas"></canvas></div>
    </div>

    <div class="image-actions">
      <div class="image-action-group">
        <select class="image-select" id="image-format" aria-label="导出格式">
          <option value="image/png">PNG</option>
          <option value="image/jpeg">JPEG</option>
          <option value="image/webp">WebP</option>
        </select>
        <select class="image-select" id="image-quality" aria-label="导出质量">
          <option value="0.92">高质量</option>
          <option value="0.8">标准质量</option>
          <option value="0.65">较小文件</option>
        </select>
      </div>
      <button class="image-button image-button-primary" id="image-export" type="button">导出图片</button>
    </div>

    <div class="image-meta">
      <span id="image-status" role="status">准备就绪。</span>
      <span class="image-local">本地处理：图片不会离开你的设备。</span>
    </div>
  </section>
</div>

<script>
  (function () {
    const elements = {
      file: document.getElementById('image-file'),
      editor: document.getElementById('image-editor'),
      canvas: document.getElementById('image-canvas'),
      brightness: document.getElementById('image-brightness'),
      contrast: document.getElementById('image-contrast'),
      saturation: document.getElementById('image-saturation'),
      brightnessValue: document.getElementById('brightness-value'),
      contrastValue: document.getElementById('contrast-value'),
      saturationValue: document.getElementById('saturation-value'),
      width: document.getElementById('image-width'),
      height: document.getElementById('image-height'),
      ratioLock: document.getElementById('image-ratio-lock'),
      fitMode: document.getElementById('image-fit-mode'),
      applySize: document.getElementById('image-apply-size'),
      preset: document.getElementById('image-size-preset'),
      rotateLeft: document.getElementById('rotate-left'),
      rotateRight: document.getElementById('rotate-right'),
      flipHorizontal: document.getElementById('flip-horizontal'),
      flipVertical: document.getElementById('flip-vertical'),
      grayscale: document.getElementById('toggle-grayscale'),
      enhance: document.getElementById('auto-enhance'),
      zoomOut: document.getElementById('zoom-out'),
      zoomIn: document.getElementById('zoom-in'),
      zoomLabel: document.getElementById('zoom-label'),
      undo: document.getElementById('image-undo'),
      reset: document.getElementById('image-reset'),
      format: document.getElementById('image-format'),
      quality: document.getElementById('image-quality'),
      export: document.getElementById('image-export'),
      status: document.getElementById('image-status')
    };

    const state = {
      image: null,
      fileName: 'image',
      rotation: 0,
      flipX: 1,
      flipY: 1,
      brightness: 100,
      contrast: 100,
      saturation: 100,
      grayscale: false,
      outputWidth: 1,
      outputHeight: 1,
      fitMode: 'cover',
      zoom: 1,
      history: []
    };

    function currentSettings() {
      return {
        rotation: state.rotation,
        flipX: state.flipX,
        flipY: state.flipY,
        brightness: state.brightness,
        contrast: state.contrast,
        saturation: state.saturation,
        grayscale: state.grayscale,
        outputWidth: state.outputWidth,
        outputHeight: state.outputHeight,
        fitMode: state.fitMode,
        zoom: state.zoom
      };
    }

    function applySettings(settings) {
      Object.assign(state, settings);
      syncControls();
      render();
    }

    function pushHistory() {
      state.history.push(currentSettings());
      if (state.history.length > 50) state.history.shift();
      elements.undo.disabled = false;
    }

    function setStatus(message) {
      elements.status.textContent = message;
    }

    function syncControls() {
      elements.brightness.value = state.brightness;
      elements.contrast.value = state.contrast;
      elements.saturation.value = state.saturation;
      elements.brightnessValue.value = `${state.brightness}%`;
      elements.contrastValue.value = `${state.contrast}%`;
      elements.saturationValue.value = `${state.saturation}%`;
      elements.zoomLabel.textContent = `${Math.round(state.zoom * 100)}%`;
      elements.width.value = state.outputWidth;
      elements.height.value = state.outputHeight;
      elements.fitMode.value = state.fitMode;
      elements.grayscale.setAttribute('aria-pressed', String(state.grayscale));
      elements.grayscale.style.borderColor = state.grayscale ? 'var(--accent, #315c96)' : '';
      elements.grayscale.style.color = state.grayscale ? 'var(--accent, #315c96)' : '';
    }

    function render() {
      if (!state.image) return;
      const sourceWidth = state.image.naturalWidth;
      const sourceHeight = state.image.naturalHeight;
      const quarterTurn = Math.abs(state.rotation % 180) === 90;
      const orientedWidth = quarterTurn ? sourceHeight : sourceWidth;
      const orientedHeight = quarterTurn ? sourceWidth : sourceHeight;
      const width = state.outputWidth;
      const height = state.outputHeight;
      const context = elements.canvas.getContext('2d');

      const sourceCanvas = document.createElement('canvas');
      sourceCanvas.width = orientedWidth;
      sourceCanvas.height = orientedHeight;
      const sourceContext = sourceCanvas.getContext('2d');
      sourceContext.save();
      sourceContext.translate(orientedWidth / 2, orientedHeight / 2);
      sourceContext.rotate(state.rotation * Math.PI / 180);
      sourceContext.scale(state.flipX, state.flipY);
      sourceContext.filter = `brightness(${state.brightness}%) contrast(${state.contrast}%) saturate(${state.saturation}%) grayscale(${state.grayscale ? 100 : 0}%)`;
      sourceContext.drawImage(state.image, -sourceWidth / 2, -sourceHeight / 2);
      sourceContext.restore();

      elements.canvas.width = width;
      elements.canvas.height = height;
      elements.canvas.style.width = `${Math.max(1, Math.round(width * state.zoom))}px`;
      elements.canvas.style.height = `${Math.max(1, Math.round(height * state.zoom))}px`;
      context.clearRect(0, 0, width, height);
      if (state.fitMode === 'stretch') {
        context.drawImage(sourceCanvas, 0, 0, width, height);
      } else {
        const ratio = state.fitMode === 'cover'
          ? Math.max(width / orientedWidth, height / orientedHeight)
          : Math.min(width / orientedWidth, height / orientedHeight);
        const drawWidth = orientedWidth * ratio;
        const drawHeight = orientedHeight * ratio;
        if (state.fitMode === 'contain') {
          context.fillStyle = '#ffffff';
          context.fillRect(0, 0, width, height);
        }
        context.drawImage(sourceCanvas, (width - drawWidth) / 2, (height - drawHeight) / 2, drawWidth, drawHeight);
      }
      syncControls();
    }

    function resetSettings() {
      state.rotation = 0;
      state.flipX = 1;
      state.flipY = 1;
      state.brightness = 100;
      state.contrast = 100;
      state.saturation = 100;
      state.grayscale = false;
      state.outputWidth = state.image ? state.image.naturalWidth : 1;
      state.outputHeight = state.image ? state.image.naturalHeight : 1;
      state.fitMode = 'cover';
      state.zoom = 1;
    }

    elements.file.addEventListener('change', function () {
      const file = elements.file.files[0];
      if (!file) return;
      const url = URL.createObjectURL(file);
      const image = new Image();
      image.onload = function () {
        if (state.image && state.image.dataset.url) URL.revokeObjectURL(state.image.dataset.url);
        image.dataset.url = url;
        state.image = image;
        state.fileName = file.name.replace(/\.[^.]+$/, '') || 'image';
        state.history = [];
        elements.undo.disabled = true;
        resetSettings();
        const availableWidth = Math.min(760, document.querySelector('.image-workspace')?.clientWidth - 48 || 760);
        state.zoom = Math.min(1, Math.max(0.1, availableWidth / image.naturalWidth));
        elements.editor.hidden = false;
        render();
        setStatus(`已打开 ${file.name} · ${image.naturalWidth} × ${image.naturalHeight}px`);
      };
      image.onerror = function () {
        URL.revokeObjectURL(url);
        setStatus('无法读取该图片，请更换文件后重试。');
      };
      image.src = url;
    });

    [['brightness', elements.brightness], ['contrast', elements.contrast], ['saturation', elements.saturation]].forEach(function ([key, input]) {
      input.addEventListener('pointerdown', pushHistory);
      input.addEventListener('keydown', function (event) {
        if (event.key.startsWith('Arrow')) pushHistory();
      });
      input.addEventListener('input', function () {
        state[key] = Number(input.value);
        render();
        setStatus('图像参数已更新。');
      });
    });

    elements.rotateLeft.addEventListener('click', function () {
      pushHistory();
      state.rotation = (state.rotation - 90) % 360;
      [state.outputWidth, state.outputHeight] = [state.outputHeight, state.outputWidth];
      render();
      setStatus('图像已向左旋转 90°。');
    });

    elements.rotateRight.addEventListener('click', function () {
      pushHistory();
      state.rotation = (state.rotation + 90) % 360;
      [state.outputWidth, state.outputHeight] = [state.outputHeight, state.outputWidth];
      render();
      setStatus('图像已向右旋转 90°。');
    });

    elements.flipHorizontal.addEventListener('click', function () {
      pushHistory();
      state.flipX *= -1;
      render();
      setStatus('图像已水平翻转。');
    });

    elements.flipVertical.addEventListener('click', function () {
      pushHistory();
      state.flipY *= -1;
      render();
      setStatus('图像已垂直翻转。');
    });

    elements.grayscale.addEventListener('click', function () {
      pushHistory();
      state.grayscale = !state.grayscale;
      render();
      setStatus(state.grayscale ? '灰度效果已启用。' : '灰度效果已关闭。');
    });

    elements.enhance.addEventListener('click', function () {
      pushHistory();
      state.brightness = 103;
      state.contrast = 108;
      state.saturation = 112;
      render();
      setStatus('已应用轻度自动增强。');
    });

    function clampDimension(value) {
      return Math.min(12000, Math.max(1, Math.round(Number(value) || 1)));
    }

    elements.width.addEventListener('input', function () {
      if (!elements.ratioLock.checked || !state.outputWidth) return;
      elements.height.value = clampDimension(Number(elements.width.value) * state.outputHeight / state.outputWidth);
    });

    elements.height.addEventListener('input', function () {
      if (!elements.ratioLock.checked || !state.outputHeight) return;
      elements.width.value = clampDimension(Number(elements.height.value) * state.outputWidth / state.outputHeight);
    });

    elements.applySize.addEventListener('click', function () {
      if (!state.image) return;
      const width = clampDimension(elements.width.value);
      const height = clampDimension(elements.height.value);
      pushHistory();
      state.outputWidth = width;
      state.outputHeight = height;
      state.fitMode = elements.fitMode.value;
      const availableWidth = Math.min(760, document.querySelector('.image-workspace')?.clientWidth - 48 || 760);
      state.zoom = Math.min(1, Math.max(0.05, availableWidth / width));
      render();
      setStatus(`输出尺寸已设为 ${width} × ${height}px。`);
    });

    elements.preset.addEventListener('change', function () {
      if (!elements.preset.value) return;
      const [width, height] = elements.preset.value.split('x').map(Number);
      elements.width.value = width;
      elements.height.value = height;
      elements.ratioLock.checked = false;
      elements.applySize.click();
    });

    elements.zoomOut.addEventListener('click', function () {
      state.zoom = Math.max(0.1, Number((state.zoom - 0.1).toFixed(2)));
      render();
    });

    elements.zoomIn.addEventListener('click', function () {
      state.zoom = Math.min(3, Number((state.zoom + 0.1).toFixed(2)));
      render();
    });

    elements.undo.addEventListener('click', function () {
      if (!state.history.length) return;
      applySettings(state.history.pop());
      elements.undo.disabled = state.history.length === 0;
      setStatus('已撤销上一步调整。');
    });

    elements.reset.addEventListener('click', function () {
      if (!state.image) return;
      pushHistory();
      resetSettings();
      render();
      setStatus('图像已恢复到初始状态。');
    });

    elements.export.addEventListener('click', function () {
      if (!state.image) return;
      const mimeType = elements.format.value;
      const quality = Number(elements.quality.value);
      const extension = mimeType === 'image/jpeg' ? 'jpg' : mimeType.split('/')[1];
      elements.canvas.toBlob(function (blob) {
        if (!blob) {
          setStatus('导出失败，请重试。');
          return;
        }
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${state.fileName}-edited.${extension}`;
        link.click();
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
        setStatus(`导出完成 · ${elements.canvas.width} × ${elements.canvas.height}px`);
      }, mimeType, quality);
    });

    window.addEventListener('keydown', function (event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z' && state.image) {
        event.preventDefault();
        elements.undo.click();
      }
    });
  })();
</script>
