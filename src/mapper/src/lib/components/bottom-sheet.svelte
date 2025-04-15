<script lang="ts">
	import '$styles/bottom-sheet.css';
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';

	let bottomSheetRef: any = $state();
	let sheetContentRef: any = $state();

	let startY: number;
	let startHeight: number;
	let currSheetHeight: number = $state(0);
	let show: boolean = $state(false);
	let isDragging: boolean = $state(false);

	interface Props {
		onClose: () => void;
		children?: Snippet;
	}

	let { onClose, children }: Props = $props();

	const updateSheetHeight = (height: number) => {
		if (sheetContentRef) {
			sheetContentRef.style.height = `${height}vh`;
		}
	};

	onMount(() => {
		show = true;
		document.body.style.overflowY = 'hidden';
		bottomSheetRef.style.height = `85vh`;
		updateSheetHeight(85);
	});

	const hideBottomSheet = () => {
		show = false;
		onClose();
		document.body.style.overflowY = 'auto';
	};

	const dragStart = (e: MouseEvent | TouchEvent) => {
		e.preventDefault();
		let pagesY: number = 0;
		if (e instanceof MouseEvent) {
			pagesY = e.pageY;
		} else if (e instanceof TouchEvent) {
			pagesY = e.changedTouches[0].screenY;
		}
		startY = pagesY;
		startHeight = parseInt(sheetContentRef.style.height);
		isDragging = true;
	};

	const dragging = (e: MouseEvent | TouchEvent) => {
		if (!isDragging) return;
		let delta: number = 0;
		if (e instanceof MouseEvent) {
			delta = startY - e.pageY;
		} else if (e instanceof TouchEvent) {
			delta = startY - e.changedTouches[0].screenY;
		}
		const newHeight = startHeight + (delta / window.innerHeight) * 100;
		bottomSheetRef.style.height = `100vh`;
		updateSheetHeight(newHeight);
	};

	const dragStop = () => {
		let sheetHeight;
		bottomSheetRef.style.height = `${currSheetHeight + 1}vh`;

		isDragging = false;
		sheetHeight = parseInt(sheetContentRef.style.height);
		currSheetHeight = sheetHeight;

		if (sheetHeight < 25) {
			hideBottomSheet();
		} else if (sheetHeight <= 75) {
			updateSheetHeight(50);
		} else {
			updateSheetHeight(85);
		}
	};

	$effect(() => {
		if (currSheetHeight) {
			dragStop();
		}
	});
</script>

<div>
	<!-- sheet container -->
	<div
		bind:this={bottomSheetRef}
		class={`sheet-container ${!show ? 'opacity-0' : 'opacity-100'}`}
	>
		<!-- sheet content -->
		<div
			bind:this={sheetContentRef}
			class={`sheet-container-content 
			${!show ? 'translate-y-[100%]' : 'translate-y-[0%]'
			} ${isDragging ? 'transition-none' : ''}`}
		>
			<div
				class="action"
				onmousedown={dragStart}
				ontouchstart={dragStart}
				onmousemove={dragging}
				ontouchmove={dragging}
				ontouchend={dragStop}
				onmouseup={dragStop}
				onmouseout={dragStop}
				role="button"
				tabindex="0"
				onblur={() => {}}
			>
				<span></span>
			</div>
			<!-- body -->
			<div class="body">
				{@render children?.()}
			</div>
		</div>
	</div>
</div>
