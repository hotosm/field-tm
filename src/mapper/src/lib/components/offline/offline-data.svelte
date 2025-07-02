<script lang="ts">
    import type { PGlite } from '@electric-sql/pglite';
    import { onMount } from 'svelte';
	import '@shoelace-style/shoelace/dist/components/carousel/carousel.js';

	import type { DbApiSubmissionType } from '$lib/types';
	import { DbApiSubmission } from '$lib/db/api-submissions';
	import { getCommonStore, getAlertStore } from '$store/common.svelte';
	import { m } from '$translations/messages.js';

	const commonStore = getCommonStore();
	const alertStore = getAlertStore();
	let db: PGlite | undefined = $derived(commonStore.db);
    let apiSubmissions: DbApiSubmissionType[] | undefined = $state([]);
    let apiFailures: DbApiSubmissionType[] | undefined = $state([]);
    let apiSubmissionsFormatted: Record<string, string>[] | undefined = $derived(
	apiSubmissions?.map((x: DbApiSubmissionType) => ({
            id: x.id.toString(),
            submissionType: getSubmissionType(x.url),
            queuedAt: formatDate(x.queued_at),
            lastAttemptAt: x.last_attempt_at ? formatDate(x.last_attempt_at) : 'N/A',
            successAt: x.success_at ? formatDate(x.success_at) : 'N/A',
            retries: x.retry_count.toString(),
            error: x.error ?? 'None'
        }))
    );

    function getSubmissionType(url: string): string {
        if (url.includes('status')) {
            return 'Feature Status Update';
        } else if (url.includes('entity')) {
            return 'New Feature';
        } else if (url.includes('submission')) {
            return 'New Submission';
        } else {
            return 'Unknown';
        }
    }

    function formatDate(isoString: string): string {
        const date = new Date(isoString);
        return new Intl.DateTimeFormat('en-GB', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
        }).format(date);
    }

    function parseCsvAndDownload(data: DbApiSubmissionType[]): void {
        if (!data || data.length === 0) {
            alertStore.setAlert({message: 'No data available to download.', variant: 'default'})
            return;
        }

        // Define CSV headers
        const headers = [
            'id',
            'url',
            'method',
            'content_type',
            'payload',
            'headers',
            'status',
            'retry_count',
            'error',
            'queued_at',
            'last_attempt_at',
            'success_at'
        ];

        // Convert each record to a CSV row
        const rows = data.map((item) => [
            item.id,
            item.url,
            item.method,
            item.content_type,
            JSON.stringify(item.payload ?? {}),
            JSON.stringify(item.headers ?? {}),
            item.status,
            item.retry_count,
            item.error ?? '',
            item.queued_at,
            item.last_attempt_at ?? '',
            item.success_at ?? ''
        ]);

        // Combine headers and rows
        const csvContent = [headers.join(','), ...rows.map((row) =>
            row.map((field) => `"${String(field).replace(/"/g, '""')}"`).join(',')
        )].join('\n');

        // Create a Blob and trigger download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');

        link.setAttribute('href', url);
        link.setAttribute('download', 'api-submissions.csv');
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    function downloadQueuedApiSubmissions(): void {
        parseCsvAndDownload(apiSubmissions);
    }

    function downloadFailedApiSubmissions(): void {
        parseCsvAndDownload(apiFailures);
    }

    onMount(async () => {
        apiSubmissions = await DbApiSubmission.allQueued(db);
        apiFailures = await DbApiSubmission.allFailed(db);
    })
</script>

<div class="data-download">
    {m['offline.total_offline_submissions']()}: {apiSubmissions?.length}
	<hot-button
		onclick={() => downloadQueuedApiSubmissions()}
		onkeydown={(e: KeyboardEvent) => {
			e.key === 'Enter' && downloadQueuedApiSubmissions();
		}}
		role="button"
		tabindex="0"
		size="small"
		class="button"
	>
		<hot-icon slot="prefix" name="download" class="icon"></hot-icon>
		<span>{m['offline.download_csv']()}</span>
	</hot-button>
    {m['offline.total_failed_submissions']()}: {apiFailures?.length}
	<hot-button
		onclick={() => downloadFailedApiSubmissions()}
		onkeydown={(e: KeyboardEvent) => {
			e.key === 'Enter' && downloadFailedApiSubmissions();
		}}
		role="button"
		tabindex="0"
		size="small"
		class="button"
	>
		<hot-icon slot="prefix" name="download" class="icon"></hot-icon>
		<span>{m['offline.download_csv']()}</span>
	</hot-button>

    {#if apiSubmissionsFormatted?.length}
        <h3>Queued API Submissions</h3>
        <sl-carousel class="scroll-hint" pagination style="--scroll-hint: 10%;">
            {#each apiSubmissionsFormatted as submission}
                <sl-carousel-item>
                    <ul>
                        <li><strong>ID:</strong> {submission.id}</li>
                        <li><strong>Type:</strong> {submission.submissionType}</li>
                        <li><strong>Queued At:</strong> {submission.queuedAt}</li>
                        <li><strong>Last Attempt At:</strong> {submission.lastAttemptAt}</li>
                        <li><strong>Retry Count:</strong> {submission.retries}</li>
                        <li><strong>Error:</strong> {submission.error}</li>
                    </ul>
                </sl-carousel-item>
            {/each}
        </sl-carousel>
    {:else}
        <p>No queued submissions found.</p>
    {/if}
</div>
