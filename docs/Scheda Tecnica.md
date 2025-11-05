================================================================
###  SCHEDA TECNICA PROGETTO: INFOTAINMENT AUTO SU RASPBERRY PI
================================================================

## 1. HARDWARE DI BASE
--------------------
  * Piattaforma: Raspberry Pi 5
  * Display: Schermo Touchscreen da 7" collegato via HDMI.
  * Uscita Audio: DAC I2S esterno basato su chip PCM5102A, collegato ai pin GPIO. L'uscita audio analogica del DAC è l'unica utilizzata.
  * Dissipazione: Sistema di raffreddamento passivo (heatsink).


## 2. SISTEMA OPERATIVO E SOFTWARE
---------------------------------
  * OS: Raspberry Pi OS Lite (64-bit, basato su Debian Bookworm), senza ambiente desktop tradizionale.
  * Server Grafico: Un server Xorg (X Server) minimale avviato manualmente per l'interfaccia grafica.
  * Stack Audio: PipeWire con WirePlumber come session manager. ALSA come strato di base per i driver.
  * Stack Bluetooth: BlueZ, con profili gestiti da PipeWire.
  * Linguaggio Applicazione: Python con libreria GUI PyQt6.


## 3. FUNZIONAMENTO E COMPORTAMENTO CHIAVE
-----------------------------------------
  * Scopo Principale: Sistema di infotainment per auto con interfaccia grafica personalizzata.
  * Funzionalità Bluetooth Audio:
      - Il Raspberry Pi agisce come un ricevitore audio (A2DP Sink).
      - L'accoppiamento è gestito per essere senza PIN o conferme ("Just Works").
  * Controllo del Volume:
      - Il DAC PCM5102A non ha un controllo del volume hardware.
      - PipeWire crea un controllo volume software virtuale chiamato "Master".
      - L'applicazione Python controlla il volume tramite comandi `amixer sset 'Master' X%`.


## 4. PUNTI CRITICI E COMPORTAMENTI NOTI
---------------------------------------
  * Lag Audio e Discoverability: Attivare la modalità "discoverable" durante lo streaming audio causa lag. La discoverability deve essere usata solo per l'accoppiamento.
  * Stabilità Connessione: La stabilità della funzionalità "speaker" dipende dal pacchetto `libspa-0.2-bluetooth` (per i codec audio avanzati).
  * Controllo Volume a Basso Livello: Per il corretto funzionamento dello slider, è stato necessario usare `alsamixer` per assicurarsi che il dispositivo di default (PipeWire) non fosse muto e che il suo controllo "Master" fosse impostato al 100%, salvando poi le impostazioni con `sudo alsactl store`.