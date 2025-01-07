<script lang="ts">
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
		class={`z-10 bottom-sheet fixed w-[100vw] left-0 bottom-0 flex items-center flex-col justify-end duration-100 ease-linear z-20 ${
			!show ? 'opacity-0 pointer-events-none' : 'opacity-100 pointer-events-none'
		}`}
	>
		<!-- sheet content -->
		<div
			style="border-top-left-radius: 25px; border-top-right-radius: 25px;"
			bind:this={sheetContentRef}
			class={`bottom-sheet-content shadow-[0px_-10px_10px_5px_rgba(0,0,0,0.05)] w-full relative bg-white max-h-[100vh] h-[50vh] max-w-[100vw] pb-6 duration-300 ease-in-out overflow-hidden md:max-w-[580px] lg:max-w-[750px] ${
				!show ? 'translate-y-[100%]' : 'translate-y-[0%] pointer-events-auto'
			} ${isDragging ? 'transition-none' : ''}`}
		>
			<div
				style={' border-top-left-radius: 1rem;'}
				class="flex justify-center py-4 sm:py-8 cursor-grab select-none w-full"
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
				<span class="h-[6px] w-[3.25rem] block bg-[#d2d2d4] rounded-full pointer-events-none"></span>
			</div>
			<!-- body -->
			<div class="overflow-y-scroll scrollbar h-[calc(100%-5rem)] sm:h-[calc(100%-6.7rem)] px-4 relative">
				{@render children?.()}
			</div>
		</div>
	</div>
</div>
