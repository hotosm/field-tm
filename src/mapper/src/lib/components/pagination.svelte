<script lang="ts">
	import '$styles/pagination.css';
	import { getPaginationRange, DOTS } from '$lib/api/get-pagination-range.ts';
	import { m } from '$translations/messages.js';

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

<div class={`pagination ${className}`}>
	<p class="showing-count">
		Showing {showing} of {totalCount} results
	</p>

	<div class="content">
		<!-- Go to Page -->
		<div class="goto-page">
			<p class="title">{m['pagination.go_to_page']()}</p>
			<input
				type="number"
				min="1"
				value={currentPageState}
				disabled={isLoading}
				class="input"
				oninput={handleInputChange}
			/>
		</div>

		{#if paginationRange.length > 1}
			<div class="actions">
				<!-- Previous Button -->
				<!-- svelte-ignore a11y_consider_explicit_label -->
				<button
					disabled={currentPage === 1}
					onclick={() => handlePageChange(currentPage - 1)}
					class={`prev-button page ${currentPage === 1 ? 'first-page' : 'not-first-page'}`}
				>
					<sl-icon name="chevron-left"></sl-icon>
				</button>

				<!-- Page Numbers -->
				{#each paginationRange as pageNumber}
					{#if pageNumber === DOTS}
						<span class="page-num-dots">&#8230;</span>
					{:else}
						<div
							class="page-num-wrapper"
							onclick={() => handlePageChange(+pageNumber)}
							onkeydown={(e) => {
								if (e.key === 'Enter') handlePageChange(+pageNumber);
							}}
							role="button"
							tabindex="0"
						>
							<p class={`page-num ${currentPage === pageNumber ? 'current-page' : 'not-current-page'}`}>
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
					class={`next-button ${currentPage === paginationRange[paginationRange.length - 1] ? 'last-page' : 'not-last-page'}`}
				>
					<sl-icon name="chevron-right"></sl-icon>
				</button>
			</div>
		{/if}
	</div>
</div>
