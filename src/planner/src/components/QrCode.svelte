<script lang="ts">
  let { text }: { text: string } = $props();
  let qr = $state<HTMLElement & { shadowRoot: ShadowRoot | null }>();

  function save() {
    const canvas = qr?.shadowRoot?.querySelector('canvas');
    if (!canvas) return;
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download = 'task-qr.png';
    a.click();
  }
</script>

<!-- Byte-mode capacity of a version 40 QR code at error correction L. -->
{#if text.length > 2900}
  <p class="hint">This task is too detailed for a QR code. Share the link instead.</p>
{:else}
<div class="stack">
  <wa-qr-code bind:this={qr} value={text} label="QR code for the task link" size="200" error-correction="L"></wa-qr-code>
  <div><wa-button size="small" appearance="outlined" onclick={save}>Download PNG</wa-button></div>
</div>
{/if}

<style>
  wa-qr-code {
    align-self: flex-start;
    padding: var(--wa-space-xs);
    background: #fff;
  }
</style>
