/* GeoPATUH — tombol "Install aplikasi" yang mudah dijangkau.
   Desktop: tombol di menubar. Ponsel/tablet: tombol melayang di bawah peta.
   Hanya tampil bila browser mengizinkan instalasi (atau di iPhone/iPad, dengan petunjuk),
   dan disembunyikan bila GeoPATUH sudah terpasang / sedang dibuka sebagai aplikasi. */
(function () {
  'use strict';
  var deferred = null, KEY = 'geoPatuhInstallHiddenUntil';
  var ios = /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  function standalone() { return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true; }
  function snoozed() { try { return Number(localStorage.getItem(KEY) || 0) > Date.now(); } catch (e) { return false; } }
  function snooze(days) { try { localStorage.setItem(KEY, String(Date.now() + days * 864e5)); } catch (e) {} }
  function toast(msg, ms) { if (window.brToast) window.brToast(msg, ms || 6000); else alert(msg); }

  var head, fab;
  function build() {
    if (head) return;
    var actions = document.querySelector('.header .head-actions');
    head = document.createElement('button');
    head.type = 'button'; head.className = 'btn gp-install-head'; head.hidden = true;
    head.innerHTML = '<i class="fas fa-download" aria-hidden="true"></i>Install Aplikasi';
    head.addEventListener('click', install);
    if (actions) actions.insertBefore(head, actions.firstChild);

    fab = document.createElement('div');
    fab.className = 'gp-install-fab'; fab.hidden = true;
    fab.innerHTML = '<button type="button" class="gp-install-go"><i class="fas fa-download" aria-hidden="true"></i>Install GeoPATUH</button>'
      + '<button type="button" class="gp-install-x" aria-label="Sembunyikan tombol install">&times;</button>';
    fab.querySelector('.gp-install-go').addEventListener('click', install);
    fab.querySelector('.gp-install-x').addEventListener('click', function () { snooze(7); refresh(); });
    document.body.appendChild(fab);
  }
  function refresh() {
    build();
    var can = !standalone() && (deferred || ios);
    head.hidden = !can;
    fab.hidden = !can || snoozed();
  }
  function install() {
    if (deferred) {
      var ev = deferred; deferred = null;
      ev.prompt();
      (ev.userChoice || Promise.resolve({})).then(function (r) { if (r && r.outcome === 'dismissed') deferred = ev; refresh(); });
      return;
    }
    if (ios) toast('Di iPhone/iPad: ketuk tombol Bagikan (kotak dengan panah ke atas), lalu pilih “Tambahkan ke Layar Utama”.', 8000);
  }
  window.addEventListener('beforeinstallprompt', function (event) { event.preventDefault(); deferred = event; refresh(); });
  window.addEventListener('appinstalled', function () { deferred = null; refresh(); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', refresh); else refresh();
  window.matchMedia('(display-mode: standalone)').addEventListener && window.matchMedia('(display-mode: standalone)').addEventListener('change', refresh);
})();
