# NEXO CONNECT: integraciones futuras

> **Estado: no implementado.** NEXO CONNECT es una propuesta para incorporar comentarios de cuentas que autoricen el acceso. No hay conexiones ni credenciales de plataformas implementadas en esta fase.

## Flujo propuesto

1. La persona propietaria de la cuenta autoriza permisos de solo lectura mediante el flujo oficial de cada plataforma.
2. Los tokens se guardan cifrados, con acceso restringido y retención limitada.
3. La ingesta incremental respeta los límites de uso, las condiciones del servicio y las políticas de cada API.
4. Los comentarios autorizados pasan por el mismo NEXO ENGINE y el clasificador de categorías.
5. Al revocar el acceso, se eliminan los tokens y los datos importados asociados, conforme a la política de retención.

No se hará scraping. Solo se procesarán cuentas autorizadas y se aplicará minimización de datos: recoger únicamente los campos necesarios para el análisis, limitar su conservación y evitar publicar información personal.

## Plataformas consideradas

### Instagram

Instagram Graph API para cuentas profesionales, mediante Facebook Login / Meta OAuth. La integración se limitaría a leer comentarios en medios propios de la cuenta que autorizó el acceso. La disponibilidad depende de la elegibilidad de la cuenta y de la aprobación de permisos por Meta.

### Facebook Pages

Graph API para leer comentarios en publicaciones de páginas autorizadas por una persona administradora. El acceso se limitaría a las páginas y al contenido incluidos en la autorización.

### YouTube

YouTube Data API v3 con OAuth de Google para consultar hilos de comentarios (`commentThreads`) de canales o videos autorizados. La ingesta deberá respetar las cuotas y políticas de la API.

### TikTok

Login Kit y las APIs oficiales disponibles para cuentas autorizadas. El acceso a productos, permisos y datos depende de la aprobación de TikTok; no se asume que la lectura de comentarios esté disponible para todas las aplicaciones o cuentas.

### X

API v2 con OAuth 2.0 PKCE para el acceso autorizado. La disponibilidad de endpoints y el volumen de uso dependen del nivel contratado; se deben considerar los tiers pagos, sus límites y las condiciones vigentes.

Los permisos concretos se definirán y verificarán contra la documentación oficial de cada plataforma antes de implementar una conexión. Este documento no fija nombres de scopes ni garantiza acceso a un endpoint.
