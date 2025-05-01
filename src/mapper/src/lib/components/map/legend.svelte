<script lang="ts">
	import '$styles/page.css';
	import '$styles/map-legend.css';
	import { m } from "$translations/messages.js";

	type entityStatusesType = { status: string; className: string };
	type Props = {
		isOpen: boolean;
	};
	const { isOpen }: Props = $props();

	const entityStatuses: entityStatusesType[] = [
		{ status: m['entity_states.READY'](), className: 'ready' },
		{ status: m['entity_states.OPENED_IN_ODK'](), className: 'opened-in-odk' },
		{ status: m['entity_states.SURVEY_SUBMITTED'](), className: 'submitted' },
		{ status: m['entity_states.MARKED_BAD'](), className: 'bad' },
	];
</script>

<div class={`map-legend ${isOpen ? 'open' : 'closed'}`}>
	<p class="title">{m['legend.features']()}</p>
	{#each entityStatuses as entityStatus}
		<div class="entity-status">
			<div
				class={`color ${entityStatus.className}`}
			></div>
			<p class="label">{entityStatus?.status}</p>
		</div>
	{/each}
</div>
