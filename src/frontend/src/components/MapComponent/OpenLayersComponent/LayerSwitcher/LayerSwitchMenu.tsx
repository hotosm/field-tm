import React, { useEffect, useState } from 'react';
import osmImg from '@/assets/images/osmLayer.png';
import satelliteImg from '@/assets/images/satelliteLayer.png';
import { useAppSelector } from '@/types/reduxTypes';
import { useLocation } from 'react-router-dom';
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from '@/components/common/Dropdown';
import { Tooltip } from '@mui/material';

export const layerIcons = {
  Satellite: satelliteImg,
  OSM: osmImg,
  'TMS Layer': satelliteImg,
};

type layerCardPropType = {
  layer: string;
  changeBaseLayerHandler: (layer: string) => void;
  active: boolean;
};

const LayerCard = ({ layer, changeBaseLayerHandler, active }: layerCardPropType) => {
  return (
    <li
      className={`fmtm-flex fmtm-justify-center fmtm-items-center fmtm-flex-col fmtm-cursor-pointer fmtm-group/layer`}
      onClick={() => changeBaseLayerHandler(layer)}
      onKeyDown={() => changeBaseLayerHandler(layer)}
    >
      {layer === 'None' ? (
        <div
          className={`fmtm-w-[3rem] fmtm-duration-200 fmtm-h-[3rem] fmtm-rounded-md group-hover/layer:fmtm-border-primaryRed fmtm-border-[2px] ${
            active ? '!fmtm-border-primaryRed' : 'fmtm-border-grey-100'
          }`}
        ></div>
      ) : (
        <img
          className={`group-hover/layer:fmtm-border-primaryRed fmtm-w-[3rem] fmtm-h-[3rem] fmtm-border-[2px] fmtm-bg-contain fmtm-rounded-md ${
            active ? '!fmtm-border-primaryRed fmtm-duration-200' : 'fmtm-border-grey-100'
          }`}
          src={layerIcons[layer] ? layerIcons[layer] : satelliteImg}
          alt={`${layer} Layer`}
        />
      )}
      <p
        className={`fmtm-body-sm fmtm-flex fmtm-justify-center group-hover/layer:fmtm-text-primaryRed fmtm-duration-200 ${
          active ? 'fmtm-text-primaryRed' : ''
        }`}
      >
        {layer}
      </p>
    </li>
  );
};

const LayerSwitchMenu = ({ map, pmTileLayerUrl = null }: { map: any; pmTileLayerUrl?: any }) => {
  const { pathname } = useLocation();
  const [baseLayers, setBaseLayers] = useState<string[]>(['OSM', 'Satellite', 'None']);
  const [hasPMTile, setHasPMTile] = useState(false);
  const [activeLayer, setActiveLayer] = useState('OSM');
  const [activeTileLayer, setActiveTileLayer] = useState('');
  const [isLayerMenuOpen, setIsLayerMenuOpen] = useState(false);
  const projectInfo = useAppSelector((state) => state.project.projectInfo);

  useEffect(() => {
    if (
      !projectInfo?.custom_tms_url ||
      !pathname.includes('project') ||
      baseLayers.includes('TMS Layer') ||
      !map ||
      baseLayers?.length === 0
    )
      return;
    setBaseLayers((prev) => [...prev, 'TMS Layer']);
  }, [projectInfo, pathname, map]);

  useEffect(() => {
    if (!pmTileLayerUrl || baseLayers.includes('Custom')) return;
    setHasPMTile(true);
    setActiveTileLayer('Custom');
  }, [pmTileLayerUrl]);

  const changeBaseLayer = (baseLayerTitle: string) => {
    const allLayers = map.getLayers();
    const filteredBaseLayers: Record<string, any> = allLayers.array_.find(
      (layer) => layer?.values_?.title == 'Base maps',
    );
    const baseLayersCollection: Record<string, any>[] = filteredBaseLayers?.values_?.layers.array_;
    baseLayersCollection
      ?.filter((bLayer) => bLayer?.values_?.title !== 'Custom')
      ?.forEach((baseLayer) => {
        if (baseLayer?.values_?.title === baseLayerTitle) {
          baseLayer.setVisible(true);
          setActiveLayer(baseLayerTitle);
        } else {
          baseLayer.setVisible(false);
        }
      });
  };

  const toggleTileLayer = (layerTitle: string) => {
    const allLayers = map.getLayers();
    const filteredBaseLayers: Record<string, any> = allLayers.array_.find(
      (layer) => layer?.values_?.title == 'Base maps',
    );
    const baseLayersCollection: Record<string, any>[] = filteredBaseLayers?.values_?.layers.array_;

    const tileLayer = baseLayersCollection?.find((baseLayer) => baseLayer?.values_?.title === layerTitle);
    if (tileLayer) {
      const isLayerVisible = tileLayer.getVisible();
      tileLayer.setVisible(!isLayerVisible);
      setActiveTileLayer(!isLayerVisible ? layerTitle : '');
    }
  };

  return (
    <div className="fmtm-w-8 fmtm-h-8 fmtm-max-w-8 fmtm-max-h-8 fmtm-rounded-full fmtm-overflow-hidden fmtm-border-[2px] fmtm-border-red-medium">
      <DropdownMenu modal={false} onOpenChange={(status) => setIsLayerMenuOpen(status)}>
        <DropdownMenuTrigger className="fmtm-outline-none">
          <Tooltip title="Base Maps" placement={isLayerMenuOpen ? 'bottom' : 'left'} arrow>
            <div
              style={{
                backgroundImage: activeLayer === 'None' ? 'none' : `url(${layerIcons[activeLayer] || satelliteImg})`,
                backgroundColor: 'white',
              }}
              className={`fmtm-relative fmtm-group fmtm-order-4 fmtm-w-8 fmtm-h-8 fmtm-cursor-pointer fmtm-bg-contain`}
            ></div>
          </Tooltip>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          className="!fmtm-p-0 fmtm-border-none fmtm-z-[45] fmtm-shadow-[0px_10px_10px_10px_rgba(0,0,0,0.1)]"
          align="end"
          alignOffset={160}
          sideOffset={-30}
        >
          <div className="fmtm-bg-white  fmtm-max-h-[20rem] fmtm-overflow-y-scroll scrollbar fmtm-flex fmtm-flex-col fmtm-gap-3 fmtm-pt-1 fmtm-rounded-lg fmtm-p-3">
            <div>
              <h6 className="fmtm-body-sm-semibold fmtm-mb-2">Base Maps</h6>
              <div className="fmtm-flex fmtm-flex-wrap fmtm-justify-between fmtm-gap-4">
                {baseLayers.map((layer) => (
                  <LayerCard
                    key={layer}
                    layer={layer}
                    changeBaseLayerHandler={changeBaseLayer}
                    active={layer === activeLayer}
                  />
                ))}
              </div>
            </div>
            {hasPMTile && (
              <div>
                <h6 className="fmtm-body-sm-semibold fmtm-mb-1">Tiles</h6>
                <div className="fmtm-flex fmtm-flex-wrap fmtm-justify-between fmtm-gap-y-2">
                  <LayerCard
                    key="Custom"
                    layer="Custom"
                    changeBaseLayerHandler={() => toggleTileLayer('Custom')}
                    active={'Custom' === activeTileLayer}
                  />
                </div>
              </div>
            )}
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default LayerSwitchMenu;
