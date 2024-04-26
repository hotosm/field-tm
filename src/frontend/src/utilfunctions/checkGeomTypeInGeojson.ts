export const checkGeomTypeInGeojson = (geojson: Record<string, any>, geomType: string): boolean => {
  if (geojson?.type === 'FeatureCollection') {
    const hasPreferredGeomType = geojson?.features?.some((feature: Record<string, any>) => {
      return feature?.geometry?.type === geomType;
    });
    return hasPreferredGeomType;
  }
  return false;
};
