<script>
	import Skeleton from '$lib/components/skeleton.svelte';
</script>

<div class="box-border h-[16rem] bg-white rounded-lg p-4 flex flex-col justify-between rounded-lg">
	<div>
		<Skeleton className="w-8 h-8 !rounded-full" />
		<div class="my-3">
			<Skeleton className="w-8 h-[14px] !rounded-full mb-1" />
			<Skeleton className="w-[80px] h-[14px] !rounded-full" />
		</div>
		<Skeleton className="w-14 h-[14px] !rounded-full mb-1" />
		<Skeleton className="w-full h-[14px] !rounded-full" />
		<Skeleton className="w-full h-[14px] !rounded-full my-1" />
		<Skeleton className="w-[50%] h-[14px] !rounded-full" />
	</div>
</div>
