<script lang="ts">
  import qrcode from 'qrcode-generator';

  let { text }: { text: string } = $props();

  const svg = $derived.by(() => {
    try {
      const qr = qrcode(0, 'L');
      qr.addData(text);
      qr.make();
      return qr.createSvgTag({ cellSize: 4, margin: 2, scalable: true });
    } catch {
      return null;
    }
  });
</script>

{#if svg}
  <!-- SVG generated locally by qrcode-generator from our own URL -->
  <div class="qr" role="img" aria-label="QR code for the task link">{@html svg}</div>
{:else}
  <p class="hint">This task is too detailed for a QR code. Share the link instead.</p>
{/if}

<style>
  .qr {
    width: 200px;
    max-width: 100%;
    background: #fff;
  }
</style>
