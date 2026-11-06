/* Pantalla de reservas: buscar libros en la feria y crear la reserva.
   Busca igual que la pantalla de Vender: filtra el catalogo que ya esta en el
   telefono (instantaneo); si todavia no cargo, le pregunta al servidor. */
(function () {
  'use strict';

  var BASE = window.BASE || '/';
  var fid = window.FERIA_ID;
  var items = [];
  var ultimos = [];
  var catalogo = [];
  var timerBusca = null;

  function $(id) { return document.getElementById(id); }
  function esc(t) {
    return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function norm(t) {
    return String(t == null ? '' : t).toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }
  function dinero(n) { return '$' + (Math.round(Number(n) * 100) / 100); }
  function msg(texto, malo) {
    var el = $('resMsg');
    if (!el) return;
    el.textContent = texto || '';
    el.style.color = malo ? '#ff8a7a' : '';
  }

  function total() {
    var t = 0;
    items.forEach(function (it) { t += it.precio * it.cantidad; });
    return t;
  }

  function dibujar() {
    var cont = $('resLista');
    if (!cont) return;
    if (!items.length) {
      cont.textContent = 'Todavía no agregaste libros.';
      return;
    }
    cont.innerHTML = items.map(function (it, i) {
      return '<div class="fila" style="gap:8px;align-items:center;padding:6px 0;' +
             'border-bottom:1px solid #2a323b">' +
             '<div class="crece"><div style="color:var(--texto)">' + esc(it.titulo) + '</div>' +
             '<div class="chico">' + dinero(it.precio) + '</div></div>' +
             '<button type="button" class="sec" data-menos="' + i + '">−</button>' +
             '<b style="min-width:24px;text-align:center">' + it.cantidad + '</b>' +
             '<button type="button" class="sec" data-mas="' + i + '">+</button>' +
             '<button type="button" class="sec" data-quitar="' + i + '">✕</button>' +
             '</div>';
    }).join('') +
      '<div class="fila" style="margin-top:8px"><div class="crece">Total</div>' +
      '<b>' + dinero(total()) + '</b></div>';
  }

  function agregarLibro(l) {
    var ya = null;
    items.forEach(function (it) { if (it.libro_id === l.id) ya = it; });
    if (ya) {
      ya.cantidad += 1;
    } else {
      items.push({ libro_id: l.id, titulo: l.titulo, precio: l.precio, cantidad: 1 });
    }
    msg('Agregado: ' + l.titulo);
    $('resCodigo').value = '';
    mostrarSugerencias([]);
    dibujar();
    try { $('resCodigo').focus(); } catch (e) {}
  }

  function mostrarSugerencias(lista) {
    ultimos = lista || [];
    var cont = $('resSugerencias');
    if (!cont) return;
    cont.innerHTML = ultimos.map(function (l, i) {
      return '<button type="button" class="sec" data-sug="' + i +
             '" style="display:block;width:100%;text-align:left;margin-bottom:4px">' +
             esc(l.titulo) + ' <span class="chico">' + dinero(l.precio) + '</span></button>';
    }).join('');
  }

  function cargarCatalogo() {
    fetch(BASE + 'api/ferias/' + fid + '/catalogo', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (x) {
        if (!x || !x.ok) return;
        catalogo = (x.libros || []).map(function (l) { l.id = l.libro_id; return l; });
      })
      .catch(function () {});
  }

  /* Filtra en memoria, como la pantalla de Vender. Devuelve false si todavia
     no hay catalogo cargado (ahi se le pregunta al servidor). */
  function buscarLocal(texto, agregarSiUno) {
    var limpio = String(texto || '').trim();
    if (/^[0-9]{8,13}$/.test(limpio)) {
      var cod = catalogo.filter(function (l) { return l.isbn === limpio; });
      if (cod.length === 1) { agregarLibro(cod[0]); return true; }
      if (catalogo.length) {
        msg('Ese código no está cargado en esta feria. Si lo tenés, cargalo primero en Stock.', true);
        return true;
      }
      return false;
    }
    if (limpio.length < 2) { mostrarSugerencias([]); msg(''); return true; }
    var q = norm(limpio);
    var lista = catalogo.filter(function (l) {
      return norm(l.titulo).indexOf(q) >= 0 ||
             norm(l.autor || '').indexOf(q) >= 0 ||
             String(l.isbn || '').indexOf(limpio) === 0;
    });
    if (!lista.length) {
      if (!catalogo.length) return false;
      mostrarSugerencias([]);
      msg('No encontré ningún libro con "' + limpio + '".', true);
      return true;
    }
    if (agregarSiUno && lista.length === 1) { agregarLibro(lista[0]); return true; }
    mostrarSugerencias(lista);
    msg(lista.length === 1 ? 'Encontré este libro:'
                           : lista.length + ' libros encontrados:');
    return true;
  }

  function buscarServidor(texto, agregarSiUno) {
    var limpio = String(texto || '').trim();
    if (limpio.length < 2) { mostrarSugerencias([]); msg(''); return; }
    fetch(BASE + 'api/ferias/' + fid + '/buscar?q=' + encodeURIComponent(limpio),
          { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (x) {
        if (!x || !x.ok) { msg('No pude buscar.', true); return; }
        var lista = x.libros || [];
        if (!lista.length) {
          mostrarSugerencias([]);
          msg('No encontré ningún libro con "' + limpio + '".', true);
          return;
        }
        if (agregarSiUno && lista.length === 1) { agregarLibro(lista[0]); return; }
        mostrarSugerencias(lista);
        msg(lista.length === 1 ? 'Encontré este libro:'
                               : lista.length + ' libros encontrados:');
      })
      .catch(function () { msg('No pude buscar.', true); });
  }

  function buscar(texto, agregarSiUno) {
    if (buscarLocal(texto, agregarSiUno)) return;
    buscarServidor(texto, agregarSiUno);
  }

  function guardar() {
    var nombre = $('resNombre').value.trim();
    var telefono = $('resTelefono').value.trim();
    if (!items.length) { msg('Agregá al menos un libro.', true); return; }
    if (!nombre) { msg('Falta el nombre de quien reserva.', true); return; }
    if (!telefono) { msg('Falta el teléfono de contacto.', true); return; }
    var b = $('btnResGuardar');
    b.disabled = true;
    fetch(BASE + 'api/ferias/' + fid + '/reservas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({
        nombre: nombre, telefono: telefono, nota: $('resNota').value.trim(),
        items: items.map(function (it) {
          return { libro_id: it.libro_id, cantidad: it.cantidad };
        })
      })
    })
      .then(function (r) { return r.json(); })
      .then(function (x) {
        b.disabled = false;
        if (!x.ok) { msg(x.error || 'No se pudo reservar.', true); return; }
        window.location.href = window.location.pathname;
      })
      .catch(function () {
        b.disabled = false;
        msg('No pude guardar la reserva.', true);
      });
  }

  /* -------------------------------------------------- camara */
  var ctlCamara = null;
  function estadoCam(texto, malo) {
    var el = $('resEstadoEscaner');
    if (!el) return;
    el.textContent = texto || '';
    el.style.color = malo ? '#ff8a7a' : '';
  }
  function abrirCamara() {
    if (ctlCamara) return;
    if (!window.Escaner) { estadoCam('No se pudo cargar el lector de codigos.', true); return; }
    if (!window.Escaner.tieneCamara()) { estadoCam('Este dispositivo no tiene camara. Escribi el codigo.', true); return; }
    if (!window.Escaner.tieneDetector() && !window.Escaner.tieneZXing()) {
      estadoCam('El navegador no puede leer codigos.', true); return;
    }
    $('resVideoCaja').classList.remove('oculto');
    $('btnResCancelarCam').classList.remove('oculto');
    $('btnResCamara').classList.add('oculto');
    estadoCam('Apuntá al código...');
    ctlCamara = window.Escaner.crear({
      video: $('resVideo'),
      continuo: false,
      onCodigo: function (codigo) {
        cerrarCamara();
        $('resCodigo').value = codigo;
        buscar(String(codigo), true);
      },
      onEstado: function (est) {
        if (est === 'escaneando') estadoCam('Apuntá al código...');
        else if (est === 'dudoso') estadoCam('No pude leer, seguí apuntando...');
        else if (est === 'sin-camara') {
          cerrarCamara();
          estadoCam('No pude abrir la camara. Revisá el permiso del navegador.', true);
        }
      }
    });
    ctlCamara.iniciar();
  }
  function cerrarCamara() {
    if (ctlCamara) { try { ctlCamara.detener(); } catch (e) {} ctlCamara = null; }
    if ($('resVideoCaja')) $('resVideoCaja').classList.add('oculto');
    if ($('btnResCancelarCam')) $('btnResCancelarCam').classList.add('oculto');
    if ($('btnResCamara')) $('btnResCamara').classList.remove('oculto');
    estadoCam('');
  }

  var campo = $('resCodigo');
  if (campo) {
    campo.addEventListener('input', function () {
      clearTimeout(timerBusca);
      var texto = campo.value;
      timerBusca = setTimeout(function () { buscar(texto, false); }, 150);
    });
    campo.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        clearTimeout(timerBusca);
        buscar(campo.value, true);
      }
    });
  }
  var btnCam = $('btnResCamara');
  if (btnCam) btnCam.addEventListener('click', abrirCamara);
  var btnCamCerrar = $('btnResCancelarCam');
  if (btnCamCerrar) btnCamCerrar.addEventListener('click', cerrarCamara);

  var btn = $('btnResAgregar');
  if (btn) btn.addEventListener('click', function () {
    clearTimeout(timerBusca);
    buscar(campo.value, true);
  });

  var sug = $('resSugerencias');
  if (sug) sug.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b) return;
    var l = ultimos[Number(b.dataset.sug)];
    if (l) agregarLibro(l);
  });

  var b2 = $('btnResGuardar');
  if (b2) b2.addEventListener('click', guardar);

  var lista2 = $('resLista');
  if (lista2) lista2.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b) return;
    if (b.dataset.mas !== undefined) {
      items[Number(b.dataset.mas)].cantidad += 1;
    } else if (b.dataset.menos !== undefined) {
      var i = Number(b.dataset.menos);
      items[i].cantidad -= 1;
      if (items[i].cantidad <= 0) items.splice(i, 1);
    } else if (b.dataset.quitar !== undefined) {
      items.splice(Number(b.dataset.quitar), 1);
    } else { return; }
    dibujar();
  });

  Array.prototype.forEach.call(document.querySelectorAll('[data-cancelar]'), function (b) {
    b.addEventListener('click', function () {
      if (!confirm('¿Cancelar esta reserva? Los libros vuelven a estar disponibles.')) return;
      fetch(BASE + 'api/reservas/' + b.dataset.cancelar + '/cancelar', {
        method: 'POST', credentials: 'same-origin'
      })
        .then(function (r) { return r.json(); })
        .then(function (x) {
          if (x.ok) window.location.href = window.location.pathname;
          else msg(x.error || 'No se pudo cancelar.', true);
        })
        .catch(function () { msg('No pude cancelar.', true); });
    });
  });

  cargarCatalogo();
  dibujar();
})();
