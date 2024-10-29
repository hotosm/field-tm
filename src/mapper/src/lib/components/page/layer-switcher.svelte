<script>
	import { clickOutside } from '$lib/utils/clickOutside.ts';

	let isOpen = false;
</script>

<div use:clickOutside on:click_outside={() => (isOpen = false)} class="relative">
	<div class="group absolute bottom-16 right-0 text-nowrap cursor-pointer" on:click={() => (isOpen = !isOpen)}>
		<hot-icon
			style="border: 1px solid #D7D7D7;"
			name="layer"
			class={`!text-[1.7rem] text-[#333333] bg-white p-2 rounded-full group-hover:text-red-600 duration-200 ${isOpen && 'text-red-600'}`}
		></hot-icon>
	</div>
	<div
		class={`absolute bottom-16 right-14 w-[10rem] bg-white rounded-md p-4 duration-200 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'} overflow-hidden`}
	>
		Layer Switcher
	</div>
</div>

<style></style>
