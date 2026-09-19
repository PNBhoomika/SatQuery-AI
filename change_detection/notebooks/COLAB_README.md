# Google Colab T4 Training Runbook (Member 3 — Change Detection)

This guide details how to fine-tune the multi-task change detection heads on Google Colab using a free T4 GPU instance, leveraging the pretrained **NASA-IBM Prithvi-EO-1.0-100M** foundation model.

---

## 1. How to Open the Notebook in Google Colab

1. Open your browser and navigate to [Google Colab](https://colab.research.google.com).
2. Click **File > Upload Notebook**.
3. Select `change_detection/notebooks/train_colab.ipynb` from this project.
4. Ensure the runtime is set to **T4 GPU**:
   - Go to **Runtime > Change runtime type**.
   - Under **Hardware accelerator**, select **T4 GPU**.
   - Click **Save**.

---

## 2. What to Upload

1. Compress your local `change_detection` folder into a ZIP archive:
   ```powershell
   Compress-Archive -Path change_detection -DestinationPath change_detection.zip
   ```
2. In Cell 4 of the notebook, when prompted, upload `change_detection.zip`.
3. The notebook will automatically extract `change_detection/` into the Colab workspace root (`/content/change_detection`).

---

## 3. Expected Training Time & Resource Usage

- **GPU**: NVIDIA T4 (15.0 GB VRAM allocated)
- **Encoder**: NASA-IBM Prithvi ViT (FROZEN — 0 backbone gradients computed)
- **Trainable Heads**:
  - `change_head`: Pixel-level change logit upsampler
  - `morphology_head`: 5-class morphology classifier
  - `type_head`: 5-class semantic change type classifier
  - `fusion`: Bi-temporal feature fusion neck
- **Batch Size**: 8 (Image size: 256x256)
- **Epochs**: 10
- **Duration**: **~15 to 25 minutes** total on T4 GPU.

---

## 4. Checkpoint Persistence in Google Drive

At training completion, Cell 8 automatically writes the following files to your Google Drive under `MyDrive/sih_member3/`:
- `MyDrive/sih_member3/best.pt`: The fine-tuned multi-task head weights.
- `MyDrive/sih_member3/Prithvi_100M.pt`: The foundation backbone weights.
- `MyDrive/sih_member3/MANIFEST.sha256`: Cryptographic checksum manifest.

---

## 5. How to Download Checkpoints Back to Local Host

1. Open Google Drive in your browser and open the folder `sih_member3`.
2. Download `best.pt` to:
   ```
   change_detection/weights/prithvi/best.pt
   ```
3. Download `MANIFEST.sha256` to:
   ```
   change_detection/weights/prithvi/MANIFEST.sha256
   ```

---

## 6. How to Verify SHA-256 Locally

Run on your Windows terminal:
```powershell
Get-FileHash change_detection/weights/prithvi/best.pt -Algorithm SHA256
```
Compare the output hash against the hash recorded in `MANIFEST.sha256`.

---

## 7. What to Do If Colab Disconnects

Colab free sessions may disconnect after periods of inactivity:
1. **Prevent Idling**: Keep the browser tab open and check on progress every 5 minutes.
2. **Reconnecting**:
   - Click **Reconnect** in the top right.
   - If the runtime was recycled, re-run Cells 1 through 4 (re-mount Google Drive and re-extract the code).
   - If training finished before the disconnect, your weights are already safely saved in `MyDrive/sih_member3/`.
