/* Aviso de cambios de precio: consulta cada 3 minutos, solo con la pantalla activa. */
window.Precios = (function () {
  'use strict';

  function esc(t) {
    return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function dinero(n) { return '$' + (Math.round(Number(n) * 100) / 100); }

  function pintarAviso(cambios) {
    var cont = document.getElementById('avisoPrecios');
    if (!cont || !cambios || !cambios.length) return;
    var items = cambios.slice(0, 8).map(function (c) {
      return '<li>' + esc(c.titulo || '—') + ': ' + dinero(c.antes) +
             ' → <b>' + dinero(c.despues) + '</b></li>';
    }).join('');
    var mas = cambios.length > 8
      ? '<div class="chico tenue" style="margin-top:4px">y ' + (cambios.length - 8) + ' más…</div>'
      : '';
    cont.innerHTML =
      '<details class="aviso-precios">' +
        '<summary class="aviso-precios-titulo">' +
          '<span>' + (cambios.length === 1 ? 'Cambió 1 precio' : 'Cambiaron ' + cambios.length + ' precios') + '</span>' +
          '<button type="button" class="aviso-precios-cerrar" data-cerrar-aviso title="Marcar como visto">×</button>' +
        '</summary>' +
        '<ul>' + items + '</ul>' + mas +
      '</details>';
  }

  function iniciar(opciones) {
    var fid = opciones.fid;
    var BASE = opciones.base || '/';
    var alCambiar = opciones.alCambiar;
    var marca = '';

    var ultimaConsulta = 0;

    function consultar() {
      /* si la app no esta a la vista no se consulta nada (menos bateria y datos) */
      if (document.visibilityState && document.visibilityState !== 'visible') return;
      ultimaConsulta = Date.now();
      var url = BASE + 'api/ferias/' + fid + '/precios' +
                (marca ? '?desde=' + encodeURIComponent(marca) : '');
      fetch(url, { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (x) {
          if (!x || !x.ok) return;
          if (x.ahora) marca = x.ahora;
          if (x.cambios && x.cambios.length) {
            pintarAviso(x.cambios);
            if (alCambiar) alCambiar(x.cambios);
          }
        })
        .catch(function () {});
    }

    document.addEventListener('click', function (e) {
      var boton = e.target && e.target.closest ? e.target.closest('[data-cerrar-aviso]') : null;
      if (!boton) return;
      e.preventDefault();
      e.stopPropagation();
      var caja = boton.closest('.aviso-precios');
      if (caja && caja.parentNode) caja.parentNode.removeChild(caja);
      fetch(BASE + 'api/ferias/' + fid + '/precios/visto',
            { method: 'POST', credentials: 'same-origin' }).catch(function () {});
    });

    setInterval(consultar, 3 * 60 * 1000);

    /* Al volver a la app se consulta en el acto, salvo que la ultima consulta
       haya sido hace menos de un minuto (asi no gasta de mas si cambia de app seguido). */
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState !== 'visible') return;
      if (Date.now() - ultimaConsulta < 60 * 1000) return;
      consultar();
    });

    consultar();   /* al entrar, para no esperar 3 minutos */
  }

  return { iniciar: iniciar, pintarAviso: pintarAviso };
})();
