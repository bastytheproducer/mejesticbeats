# TODO: Integrar PayPal como método de pago

- [x] Instalar dependencias necesarias (requests para Python)
- [x] Configurar credenciales de PayPal (Sandbox inicialmente)
- [x] Crear endpoint en server.py para crear órdenes de PayPal
- [x] Crear endpoint para capturar pagos
- [x] Actualizar checkout.js para integrar PayPal Buttons SDK
- [x] Actualizar checkout.html para incluir PayPal buttons
- [ ] Probar integración con sandbox
- [ ] Configurar para producción cuando esté listo

## Próximos pasos:
1. Obtener credenciales de PayPal Sandbox desde https://developer.paypal.com/
2. Reemplazar 'TU_CLIENT_ID_SANDBOX' y 'TU_CLIENT_SECRET_SANDBOX' en server.py
3. Reemplazar 'TU_CLIENT_ID_SANDBOX' en checkout.html
4. Probar la integración
5. Para producción, cambiar URLs y credenciales
