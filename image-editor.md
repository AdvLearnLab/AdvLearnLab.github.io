---
layout: homepage
title: Image Editor
permalink: /image-editor.html
---

<div class="image-tool">
  <header class="image-tool-hero">
    <span>Local Image Utility</span>
    <h1>图像编辑工具</h1>
    <p>上传图片后进行缩放、旋转、翻转和色彩调整，再导出为常用图像格式。所有处理都在浏览器本地完成。</p>
  </header>

  <label class="image-upload" for="image-file">
    <span>
      <strong>打开一张图片</strong>
      <span>支持 PNG、JPEG、WebP、BMP 和 GIF 静态帧</span>
    </span>
    <input id="image-file" type="file" accept="image/png,image/jpeg,image/webp,image/bmp,image/gif">
  </label>

  <section class="image-editor" id="image-editor" hidden>
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
      elements.grayscale.setAttribute('aria-pressed', String(state.grayscale));
      elements.grayscale.style.borderColor = state.grayscale ? 'var(--accent, #315c96)' : '';
      elements.grayscale.style.color = state.grayscale ? 'var(--accent, #315c96)' : '';
    }

    function render() {
      if (!state.image) return;
      const quarterTurn = Math.abs(state.rotation % 180) === 90;
      const sourceWidth = state.image.naturalWidth;
      const sourceHeight = state.image.naturalHeight;
      const width = quarterTurn ? sourceHeight : sourceWidth;
      const height = quarterTurn ? sourceWidth : sourceHeight;
      const context = elements.canvas.getContext('2d');

      elements.canvas.width = width;
      elements.canvas.height = height;
      elements.canvas.style.width = `${Math.max(1, Math.round(width * state.zoom))}px`;
      elements.canvas.style.height = `${Math.max(1, Math.round(height * state.zoom))}px`;
      context.clearRect(0, 0, width, height);
      context.save();
      context.translate(width / 2, height / 2);
      context.rotate(state.rotation * Math.PI / 180);
      context.scale(state.flipX, state.flipY);
      context.filter = `brightness(${state.brightness}%) contrast(${state.contrast}%) saturate(${state.saturation}%) grayscale(${state.grayscale ? 100 : 0}%)`;
      context.drawImage(state.image, -sourceWidth / 2, -sourceHeight / 2);
      context.restore();
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
      render();
      setStatus('图像已向左旋转 90°。');
    });

    elements.rotateRight.addEventListener('click', function () {
      pushHistory();
      state.rotation = (state.rotation + 90) % 360;
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
