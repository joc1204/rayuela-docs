/* Stock: escanear, confirmar cantidad, ingresar ejemplares a la feria. */
(function () {
  'use strict';
  var fid = window.FERIA_ID;
  var BASE = window.BASE || '/';

  var libros = [];
  var ctl = null;
  var pendiente = null;
  var EDITABLE = false;       // el permiso real lo manda el servidor
  var enviando = false;
  var avisoT = null;

  /* aviso grande y centrado (para que se lea de lejos) */
  function avisoGrande(texto, esError, ms) {
    var a = document.getElementById('avisoGrande');
    if (!a) { estado(texto, esError); return; }
    a.textContent = texto;
    a.className = 'toast-grande abajo' + (esError ? ' error' : '');
    a.classList.remove('oculto');
    if (avisoT) clearTimeout(avisoT);
    avisoT = setTimeout(function () { a.classList.add('oculto'); },
                        ms || (esError ? 4000 : 3000));
  }

  var video = document.getElementById('video');
  var cajaVideo = document.getElementById('videoCaja');
  var btnEscanear = document.getElementById('btnEscanear');
  var btnCancelar = document.getElementById('btnCancelarCam');
  var panel = document.getElementById('panel');
  var panelTitulo = document.getElementById('panelTitulo');
  var panelPrecio = document.getElementById('panelPrecio');
  var panelHint = document.getElementById('panelHint');
  var estadoEl = document.getElementById('estadoEscaner');
  var listaEl = document.getElementById('lista');
  var cuentaEl = document.getElementById('cuenta');
  var cantEl = document.getElementById('cantidad');

  function esc(t) {
    return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function dinero(n) { return '$' + (Math.round(Number(n) * 100) / 100); }
  function estado(t, error) {
    estadoEl.textContent = t || '';
    estadoEl.className = 'estado-escaner' + (error ? ' error' : '');
  }
  function vibrar(ms) {
    if (navigator.vibrate) { try { navigator.vibrate(ms); } catch (e) {} }
  }
  function total(l) { return (l.llevados || 0) + (l.repuestos || 0); }

  /* ------------------------------------------------ lista */
  function cargar() {
    fetch(BASE + 'api/ferias/' + fid + '/catalogo', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (x) {
        if (!x.ok) { estado(x.error || 'No pude leer la feria.', true); return; }
        EDITABLE = !!x.puede_editar;
        libros = x.libros.map(function (l) { l.id = l.libro_id; return l; });
        dibujar();
      })
      .catch(function () { estado('No pude conectar.', true); });
  }

  function dibujar() {
    if (!libros.length) {
      listaEl.innerHTML = '<p class="tenue">Todavía no hay libros en esta feria.</p>';
      cuentaEl.textContent = '';
      return;
    }
    listaEl.innerHTML = libros.map(function (l) {
      var detalle = 'lleva ' + l.llevados;
      if (l.repuestos) detalle += ' · repuesto ' + l.repuestos;
      detalle += ' · vendidos ' + l.vendidos + ' · disp. ' + l.disponible;
      var acciones = EDITABLE
        ? '<button class="peligro" type="button" data-quitar="' + l.fl_id + '">\u2715</button>'
        : '';
      return '<div class="libro-fila">' +
        '<div class="crece">' +
        '<div class="titulo">' + esc(l.titulo) + '</div>' +
        '<div class="chico tenue">' + esc(detalle) + '</div>' +
        '</div>' +
        '<span class="cant">\u00D7' + total(l) + '</span>' +
        acciones +
        '</div>';
    }).join('');
    cuentaEl.textContent = '(' + libros.length + ')';
  }

  function ordenar() {
    libros.sort(function (a, b) { return String(a.titulo).localeCompare(String(b.titulo)); });
  }

  function ponerLibro(nuevo) {
    nuevo.id = nuevo.libro_id;
    var i = -1;
    for (var k = 0; k < libros.length; k++) {
      if (libros[k].fl_id === nuevo.fl_id) { i = k; break; }
    }
    if (i >= 0) { libros[i] = nuevo; } else { libros.push(nuevo); }
    ordenar();
    dibujar();
  }

  function quitar(flid) {
    if (!confirm('Quitar este libro de la feria?')) return;
    fetch(BASE + 'api/feria_libros/' + flid + '/quitar', {
      method: 'POST', credentials: 'same-origin'
    })
      .then(function (r) {
        if (r.status === 403) { estado('No tenés permiso para quitar libros.', true); return null; }
        return r.json();
      })
      .then(function (x) {
        if (!x) return;
        if (!x.ok) { estado(x.error || 'No pude quitar.', true); return; }
        libros = libros.filter(function (l) { return l.fl_id !== flid; });
        dibujar();
        estado('Libro quitado.');
      })
      .catch(function () { estado('No pude conectar.', true); });
  }

  /* ------------------------------------------------ camara */
  function abrirCamara() {
    if (ctl) return;
    if (!window.Escaner.tieneCamara()) {
      estado('Este dispositivo no tiene camara. Escribi el codigo abajo.', true);
      return;
    }
    if (!window.Escaner.tieneDetector() && !window.Escaner.tieneZXing()) {
      estado('El navegador no puede leer codigos. Escribilo a mano abajo.', true);
      return;
    }
    cajaVideo.classList.remove('oculto');
    btnCancelar.classList.remove('oculto');
    btnEscanear.classList.add('oculto');
    estado('Apuntá al código...');
    ctl = window.Escaner.crear({
      video: video,
      continuo: false,
      onCodigo: function (codigo) {
        cerrarCamara();
        consultar(codigo);
      },
      onEstado: function (est) {
        if (est === 'escaneando') estado('Apuntá al código...');
        else if (est === 'dudoso') estado('No pude leer, seguí apuntando...');
        else if (est === 'sin-camara') {
          cerrarCamara();
          estado('No pude abrir la camara. Revisá el permiso.', true);
        }
      }
    });
    ctl.iniciar();
  }

  function cerrarCamara() {
    if (ctl) { ctl.detener(); ctl = null; }
    cajaVideo.classList.add('oculto');
    btnCancelar.classList.add('oculto');
    btnEscanear.classList.remove('oculto');
  }

  /* ------------------------------------------------ confirmacion */
  function consultar(codigo) {
    var limpio = window.Escaner.limpiar(codigo);
    if (!window.Escaner.checksumEan13(limpio)) {
      estado('Ese código no parece válido (13 números).', true);
      vibrar(120);
      return;
    }
    var libro = null;
    for (var i = 0; i < libros.length; i++) {
      if (libros[i].isbn === limpio) { libro = libros[i]; break; }
    }
    if (libro) {
      document.getElementById('codigo').value = '';
      mostrarPanel(libro, true);
      return;
    }
    estado('Buscando en el sistema...');
    fetch(BASE + 'api/ferias/' + fid + '/consultar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ codigo: limpio })
    })
      .then(function (r) {
        if (r.status === 403) { estado('No tenés permiso para ingresar stock.', true); return null; }
        return r.json();
      })
      .then(function (x) {
        if (!x) return;
        if (!x.ok) {
          estado(x.error || 'No pude consultar el libro.', true);
          vibrar(120);
          return;
        }
        var l = x.libro;
        l.id = l.libro_id;
        l.llevados = 0;
        l.repuestos = 0;
        l.vendidos = 0;
        l.disponible = 0;
        document.getElementById('codigo').value = '';
        mostrarPanel(l, false);
      })
      .catch(function () { estado('No pude conectar.', true); });
  }

  function mostrarPanel(libro, yaEsta) {
    pendiente = libro;
    panelTitulo.textContent = libro.titulo;
    panelPrecio.textContent = dinero(libro.precio);
    panelHint.textContent = yaEsta
      ? 'Lleva ' + libro.llevados + ' · repuesto ' + libro.repuestos +
        ' · disponible ' + libro.disponible
      : 'No está en la feria todavía: se agrega ahora.';
    cantEl.value = '1';
    panel.classList.remove('oculto');
    estado('');
    vibrar(60);
    try { cantEl.focus(); cantEl.select(); } catch (e) {}
    panel.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }

  function cerrarPanel() {
    pendiente = null;
    panel.classList.add('oculto');
    try { btnEscanear.focus(); } catch (e) {}
  }

  function sumarCantidad(delta) {
    var v = parseInt(cantEl.value || '1', 10);
    if (isNaN(v)) v = 1;
    cantEl.value = String(Math.max(1, Math.min(999, v + delta)));
  }

  function aceptar() {
    if (!pendiente || enviando) return;
    var cantidad = Math.max(1, Math.min(999, parseInt(cantEl.value || '1', 10) || 1));
    var boton = document.getElementById('btnAceptar');
    enviando = true;
    boton.disabled = true;
    fetch(BASE + 'api/ferias/' + fid + '/ingresar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ libro_id: pendiente.id, cantidad: cantidad })
    })
      .then(function (r) {
        if (r.status === 403) { estado('No tenés permiso para ingresar stock.', true); return null; }
        return r.json();
      })
      .then(function (x) {
        enviando = false;
        boton.disabled = false;
        if (!x) return;
        if (!x.ok) { estado(x.error || 'No pude ingresar.', true); return; }
        ponerLibro(x.libro);
        cerrarPanel();
        vibrar(70);
        estado('Ingresado: ' + x.libro.titulo + ' (+' + x.cantidad + ')');
      })
      .catch(function () {
        enviando = false;
        boton.disabled = false;
        estado('No pude conectar.', true);
      });
  }

  /* ------------------------------------------------ eventos */
  btnEscanear.addEventListener('click', abrirCamara);
  btnCancelar.addEventListener('click', function () { cerrarCamara(); estado(''); });
  document.getElementById('btnBuscar').addEventListener('click', function () {
    consultar(document.getElementById('codigo').value);
  });
  document.getElementById('codigo').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); consultar(this.value); }
  });
  document.getElementById('btnMenos').addEventListener('click', function () { sumarCantidad(-1); });
  document.getElementById('btnMas').addEventListener('click', function () { sumarCantidad(1); });
  cantEl.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); aceptar(); }
  });
  document.getElementById('btnAceptar').addEventListener('click', aceptar);
  document.getElementById('btnDescartar').addEventListener('click', cerrarPanel);

  listaEl.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b) return;
    if (!EDITABLE) { estado('No tenés permiso para modificar la carga.', true); return; }
    if (b.dataset.quitar) quitar(Number(b.dataset.quitar));
  });

  document.addEventListener('visibilitychange', function () {
    if (document.hidden && ctl) {
      cerrarCamara();
      estado('Camara cerrada. Tocá Escanear para seguir.');
    }
  });

  /* ------------------------------------------------ link del mapa */
  function copiarViejo(link) {
    try {
      var ta = document.createElement('textarea');
      ta.value = link;
      ta.style.position = 'fixed';
      ta.style.top = '-1000px';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      return true;
    } catch (e) {
      return false;
    }
  }

  function copiarTexto(link) {
    var listo = function () {
      avisoGrande('Link del mapa copiado\n' + link, false, 5000);
    };
    var fallo = function () {
      if (copiarViejo(link)) { listo(); return; }
      avisoGrande('No pude copiar. El link es:\n' + link, true, 8000);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(link).then(listo, fallo);
    } else {
      fallo();
    }
  }

  function mensajeUbicacion(error) {
    if (!window.isSecureContext) {
      return 'La ubicación solo funciona con https://.\nAbrí la app desde https://ferias.rayuelalaplata.com.ar';
    }
    var codigo = error && error.code;
    if (codigo === 1) {
      return 'El navegador tiene bloqueada la ubicación para esta página.\n' +
             'Tocá el candado al lado de la dirección → Ubicación → Permitir, y recargá.';
    }
    if (codigo === 2) {
      return 'El teléfono no está dando la ubicación.\nEncendé la Ubicación/GPS y probá de nuevo.';
    }
    if (codigo === 3) {
      return 'La ubicación tardó demasiado.\nProbá otra vez, mejor al aire libre.';
    }
    return 'No pude obtener la ubicación.\nRevisá el permiso del navegador.';
  }

  var bLink = document.getElementById('btnCopiarLink');
  if (bLink) {
    bLink.addEventListener('click', function () {
      if (!navigator.geolocation) {
        avisoGrande('Este dispositivo no da la ubicación.', true);
        return;
      }
      avisoGrande('Buscando la ubicación...');
      navigator.geolocation.getCurrentPosition(function (p) {
        var lat = p.coords.latitude.toFixed(6);
        var lon = p.coords.longitude.toFixed(6);
        copiarTexto('https://maps.google.com/?q=' + lat + ',' + lon);
      }, function (error) {
        avisoGrande(mensajeUbicacion(error), true);
      }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
    });
  }

  cargar();
  /* aviso de precios: consulta cada 3 minutos, solo con la pantalla activa */
  window.Precios.iniciar({
    fid: fid,
    base: BASE,
    alCambiar: function (cambios) {
      cambios.forEach(function (c) {
        for (var i = 0; i < libros.length; i++) {
          if (libros[i].libro_id === c.libro_id) { libros[i].precio = c.despues; break; }
        }
      });
      dibujar();
    }
  });
})();
