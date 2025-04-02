<script lang="ts">
	import { getPaginationRange, DOTS } from '$lib/utils/getPaginationRange';
	import { m } from "$translations/messages.js";

	type propsType = {
		showing: number;
		totalCount: number;
		currentPage: number;
		pageSize: number;
		handlePageChange: (value: number) => void;
		isLoading: boolean;
		className: string;
	};

	const { showing, totalCount, currentPage, pageSize, handlePageChange, isLoading, className }: propsType = $props();

	let paginationRange: (number | string)[] = $state([]);
	let currentPageState: number = $state(currentPage);

	$effect(() => {
		paginationRange = getPaginationRange({ currentPage, totalCount, pageSize });
	});

	function handleInputChange(event: Event) {
		let value = +event?.target?.value;
		const maxPage = paginationRange[paginationRange.length - 1] as number;

		if (value > maxPage) value = maxPage;
		if (value < 1) value = 1;

		currentPageState = value;
		handlePageChange(value);
	}
</script>

<div
	class={`bottom-0 flex items-center justify-between flex-col sm:flex-row bg-white py-2 px-11 shadow-black shadow-2xl z-50 gap-1 ${className} box-border`}
>
	<p class="text-[0.75rem] leading-normal font-normal text-[#484848]">
		Showing {showing} of {totalCount} results
	</p>

	<div class="flex flex-wrap justify-center gap-x-6 gap-y-1">
		<!-- Go to Page -->
		<div class="flex flex-1 items-center justify-center gap-2 md:pr-6">
			<p class="text-[0.75rem] leading-normal font-normal whitespace-nowrap text-[#484848]">{m['pagination.go_to_page']()}</p>
			<input
				type="number"
				min="1"
				value={currentPageState}
				disabled={isLoading}
				class="body-md outline-none border border-[#D0D5DD] rounded-lg w-8 h-8 p-1"
				oninput={handleInputChange}
			/>
		</div>

		{#if paginationRange.length > 1}
			<div class="flex items-center gap-2 overflow-x-auto max-sm:w-[100%] max-sm:justify-center">
				<!-- Previous Button -->
				<!-- svelte-ignore a11y_consider_explicit_label -->
				<button
					disabled={currentPage === 1}
					onclick={() => handlePageChange(currentPage - 1)}
					class={`w-5 h-5 min-w-5 min-h-5 rounded-full flex items-center justify-center border-[0px] ${currentPage === 1 ? 'cursor-not-allowed text-[#BDBDBD]' : 'hover:bg-[#FFEDED] duration-100 hover:text-[#B11E20]'}`}
				>
					<hot-icon name="chevron-left" class="!text-[0.8rem] text-[#B11E20] cursor-pointer"></hot-icon>
				</button>

				<!-- Page Numbers -->
				{#each paginationRange as pageNumber}
					{#if pageNumber === DOTS}
						<span class="text-[0.75rem] leading-normal font-normal-regular text-black-600">&#8230;</span>
					{:else}
						<div
							class={`grid h-8 cursor-pointer place-items-center px-3`}
							onclick={() => handlePageChange(+pageNumber)}
							onkeydown={(e) => {
								if (e.key === 'Enter') handlePageChange(+pageNumber);
							}}
							role="button"
							tabindex="0"
						>
							<p
								class={`text-[0.75rem] leading-normal font-normal ${currentPage === pageNumber ? '!font-bold text-[#D73F37]' : 'texy-[#484848] text-[#212121]'}`}
							>
								{pageNumber}
							</p>
						</div>
					{/if}
				{/each}

				<!-- Next Button -->
				<!-- svelte-ignore a11y_consider_explicit_label -->
				<button
					disabled={currentPage === paginationRange[paginationRange.length - 1]}
					onclick={() => handlePageChange(currentPage + 1)}
					class={`w-5 h-5 min-w-5 min-h-5 rounded-full flex items-center justify-center border-[0px] ${currentPage === paginationRange[paginationRange.length - 1] ? 'cursor-not-allowed text-[#BDBDBD]' : 'hover:bg-[#FFEDED] duration-100 hover:text-[#B11E20]'}`}
				>
					<hot-icon name="chevron-right" class="!text-[0.8rem] text-[#B11E20] cursor-pointer"></hot-icon>
				</button>
			</div>
		{/if}
	</div>
</div>
