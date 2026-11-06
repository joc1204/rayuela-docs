/* Compartir los reportes de la feria: usa el menu del celular (WhatsApp, email, etc.).
   Si el navegador no puede adjuntar archivos, descarga el ZIP. */
(function () {
  'use strict';

  var boton = document.getElementById('btnCompartir');
  var estado = document.getElementById('estadoCompartir');
  var datos = document.getElementById('datosReportes');
  if (!boton || !datos) return;

  var archivos;
  try { archivos = JSON.parse(datos.textContent || '[]'); } catch (e) { archivos = []; }

  function avisar(texto, malo) {
    if (!estado) return;
    estado.textContent = texto || '';
    estado.style.color = malo ? '#ff8a7a' : '';
  }

  function bajarZip() {
    avisar('Tu navegador no puede compartir archivos: te descargo el ZIP para que lo adjuntes.');
    window.location.href = boton.dataset.zip;
  }

  boton.addEventListener('click', function () {
    if (!archivos.length) { avisar('No hay reportes para compartir.', true); return; }
    if (!navigator.share) { bajarZip(); return; }

    avisar('Preparando los archivos...');
    Promise.all(archivos.map(function (r) {
      return fetch(r.url, { credentials: 'same-origin' })
        .then(function (respuesta) {
          if (!respuesta.ok) throw new Error('no pude bajar ' + r.archivo);
          return respuesta.blob();
        })
        .then(function (blob) {
          return new File([blob], r.archivo, { type: 'text/csv' });
        });
    })).then(function (lista) {
      if (navigator.canShare && !navigator.canShare({ files: lista })) {
        bajarZip();
        return;
      }
      avisar('Elegí WhatsApp o el email en el menú...');
      return navigator.share({
        files: lista,
        title: 'Reportes de la feria',
        text: 'Reportes del cierre'
      }).then(function () { avisar(''); });
    }).catch(function (error) {
      if (error && error.name === 'AbortError') { avisar(''); return; }
      bajarZip();
    });
  });
})();
