import type { PGlite } from '@electric-sql/pglite';

import { DbApiSubmission } from '$lib/db/api-submissions.ts';
import { trySendingSubmission } from '$lib/api/fetch.ts';
import { getCommonStore, getAlertStore } from '$store/common.svelte.ts';
import { getLoginStore } from '$store/login.svelte';

const commonStore = getCommonStore();
const alertStore = getAlertStore();
const loginStore = getLoginStore();

function wait(ms: number) {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Iterate and attempt to send all pending API submissions from the local database.
 *
 * This function is triggered in two scenarios:
 *  - Automatically when coming back online (debounced via $effect)
 *  - Manually via the sync button in the map UI
 *
 * Each submission is sent sequentially. If the API acknowledges receipt (status becomes 'RECEIVED'),
 * it is considered a success. Failures are logged but not retried immediately (they remain in 'PENDING').
 *
 * Syncing status is tracked via `commonStore.offlineDataIsSyncing` and alerts are shown after each attempt.
 */
async function iterateAndSendOfflineSubmissions(db: PGlite): Promise<boolean> {
	if (!db) return false;

	// Count remaining pending submissions
	const total = await DbApiSubmission.count(db);
	if (total === 0) return true; // Nothing to be done

	const queuedSubmissions = await DbApiSubmission.allQueued(db);
	const hasUserSub = queuedSubmissions?.some((row) => !!row?.user_sub);
	const authDetails = loginStore.getAuthDetails;

	// if user made offline submissions while logged in and not logged in during online sync, prompt them to log in before before uploading submissions
	if (hasUserSub && !authDetails) {
		alertStore.setAlert({
			message: 'You must be logged in to send offline data.',
			variant: 'danger',
		});
		loginStore.toggleLoginModal(true);
		return false;
	}

	commonStore.setOfflineDataIsSyncing(true);
	alertStore.setAlert({
		message: `Found ${total} offline submissions.`,
		variant: 'default',
	});

	let sent = 0;
	let failed = 0;
	let processed = 0; // How many attempts made (success + fail)

	// Use `while (true)` for continued iteration, as we manually break loop below
	// It's safer than `while (processed < total)` in this dynamic context
	while (true) {
		const row = await DbApiSubmission.next(db);
		if (!row) break; // No more pending entries

		const success = await trySendingSubmission(db, row);

		if (success) {
			sent++;
			// Commented, as this is bad ux if multiple send in quick succession
			// alertStore.setAlert({
			// 	message: `Successfully sent offline data ${sent}/${total} to API`,
			// 	variant: 'success'
			// });
			await DbApiSubmission.deleteById(db, row.id);
			commonStore.setOfflineSyncPercentComplete((sent / total) * 100);
			// Wait 1 second until next API call
			await wait(1000);
		} else {
			alertStore.setAlert({
				message: `Failed to send offline data ${sent + 1}/${total} to API — stopping sync.`,
				variant: 'danger',
			});
			failed++;
			await DbApiSubmission.moveToFailedTable(db, row.id);
		}
	}

	commonStore.setOfflineSyncPercentComplete(null);
	commonStore.setOfflineDataIsSyncing(false);

	if (sent + failed === total) {
		const remainingSubmissions = await DbApiSubmission.count(db);
		if (remainingSubmissions !== 0) {
			alertStore.setAlert({
				message: `Offline sync incomplete: ${remainingSubmissions} remaining to send.`,
				variant: 'warning',
			});
			return false;
		}

		alertStore.setAlert({
			message: `Finished sending offline data.`,
			variant: 'success',
		});
		return true;
	} else {
		alertStore.setAlert({
			message: `Offline sync incomplete: ${sent}/${total} submissions sent.`,
			variant: 'warning',
		});
		return false;
	}
}

export { trySendingSubmission, iterateAndSendOfflineSubmissions };
