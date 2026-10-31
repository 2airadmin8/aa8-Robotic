/**
 * Sales email URL helper for the EXISTING airadmin8-haishin Script.
 * Preserve the delivery ID in the official catalogue URL. Recipient never
 * receives a personal email/address embedded in a link. Don't touch send gates.
 */
function buildTrackedCatalogUrl_(deliveryId) {
  const id=String(deliveryId||'').trim();
  if(!/^(?:DLV|RSJ)-[A-Za-z0-9._-]{5,153}$/.test(id))return 'https://robotics.air-admin8.co.jp/products.html';
  return 'https://robotics.air-admin8.co.jp/products.html?rid=' + encodeURIComponent(id)
    + '&utm_source=university_sales&utm_medium=email&utm_campaign=ai_robot_intro';
}
