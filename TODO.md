# TODO: Integrate WebPay Links and Update Prices to CLP

## Steps to Complete

1. **Update prices in index.html**: Change all beat prices from USD format (e.g., $20) to CLP format (e.g., $20.000 CLP) for all beats listed.
   - [x] Beat Verano Reggaeton: $20.000 CLP
   - [x] Beat 2025 Verano Trap: $25.000 CLP
   - [x] Beat Rellax Reggaeton: $22.000 CLP
   - [x] Beat Hip Hop Piano Gigant: $28.000 CLP
   - [x] Beat Sin Frontera: $30.000 CLP
   - [x] Beat Trap Navideño Chilling: $26.000 CLP

2. **Update prices in checkout.js**: Modify the beatData object to reflect the new CLP prices (e.g., '$20.000 CLP' instead of '$20') for all beats.
   - [x] Updated beatData object with CLP prices

3. **Modify buyBeat function in script.js**: Update the buyBeat function to redirect directly to the provided WebPay links for all beats, mapping each beat name to its corresponding WebPay URL.
   - [x] Beat Verano Reggaeton: https://www.webpay.cl/form-pay/329024
   - [x] Beat 2025 Verano Trap: https://www.webpay.cl/form-pay/329189
   - [x] Beat Trap Navideño Chilling: https://www.webpay.cl/form-pay/329222
   - [x] Beat Rellax Reggaeton: https://www.webpay.cl/form-pay/329218
   - [x] Beat Sin Frontera: https://www.webpay.cl/form-pay/329220
   - [x] Beat Hip Hop Piano Gigant: https://www.webpay.cl/form-pay/329219

4. **Verify changes**: Ensure all prices are updated correctly and redirects work as expected.
   - [x] All prices updated to CLP format
   - [x] buyBeat function now redirects to WebPay links for all beats
