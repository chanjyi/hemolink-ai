/* HemoLink service worker — shows web-push alerts (urgent requests, reminders…) and opens the app on tap.
   It deliberately has no fetch handler: pages always load fresh from the server. */
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (err) {
    data = { title: "HemoLink", body: event.data ? event.data.text() : "" };
  }
  const urgent = data.tag === "urgent_alert";
  event.waitUntil(
    self.registration.showNotification(data.title || "HemoLink", {
      body: data.body || "",
      icon: "/static/icon-192.png",
      badge: "/static/icon-192.png",
      tag: data.tag || "hemolink",
      renotify: urgent,
      requireInteraction: urgent,
      vibrate: urgent ? [200, 100, 200] : undefined,
      data: { url: data.url || "/" },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = new URL(event.notification.data?.url || "/", self.location.origin).href;
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      for (const c of list) {
        if (c.url.startsWith(self.location.origin)) {
          c.focus();
          return c.navigate(url);
        }
      }
      return self.clients.openWindow(url);
    }),
  );
});
