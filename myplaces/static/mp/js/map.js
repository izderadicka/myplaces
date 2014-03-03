var showMap= function(groupId, placeId) {
	var mapObject=createMap('map', 
			{backControl:'topleft', 
		locateControl:'topleft', 
		closeAsBackControl: 'topright',
		layersControl:'topright'});
		mapObject.displayGroup(groupId, placeId);
		
};

var showMapAsSelector=function(location, updateLocation, pointInfo) {
	var mapObject=createMap('map', 
		{locateControl:'topleft', 
		doneControl: "topright",
		});
	
	mapObject.displayLocation(location, updateLocation, pointInfo);
	
	
};

var createMap = function(elementId, options) {
    var baseURL='/mp/geojson/group/99999/',
    map, 
    basicLayers = {}, 
    overlayLayers = {}, 
    currentPosition = null, 
    mapHistory = [],
    controls={};
    
	var basicMap = function(elementId, options) {
		map = L.map(elementId);
		map.attributionControl.setPrefix('');
		basicLayers.OSM = L
				.tileLayer(
						'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
						{
							attribution : '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
							maxZoom : 18,
							noWrap : true
						}).addTo(map);
		
		basicLayers["MapQuest-OSM"] = L
		.tileLayer(
				'http://otile1.mqcdn.com/tiles/1.0.0/map/{z}/{x}/{y}.png',
				{
					attribution : '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
					maxZoom : 18,
					noWrap : true
				});
		
		basicLayers["MapQuest-Open Aerial"] = L
		.tileLayer(
				'http://otile1.mqcdn.com/tiles/1.0.0/sat/{z}/{x}/{y}.png',
				{
					attribution : 'Portions Courtesy NASA/JPL-Caltech and U.S. Depart. of Agriculture, Farm Service Agency',
					maxZoom : 18,
					noWrap : true
				});
		
		if (options.backControl) {
			addBackControl(mapOptions.backControl);
		}

		if (options.locateControl) {
			addLocateControl(mapOptions.locateControl);
		}

		if (options.closeAsBackControl) {
			addCloseAsBackControl(options.layersControl);
		}
		
		if (options.doneControl) {
			addDoneControl(options.doneControl);
		}
		
		if (options.layersControl) {
			addLayersControl(options.layersControl);
		}

		if (options.center && options.zoom) {
			map.setView(options.center, options.zoom);
		}

		return map;
	};

	var mapOptions = $.extend({
		backControl : null,
		locateControl : null,
		layersControl : null,
		doneControl: null,
		center : null, // [lat. lng]
		zoom : null // [0-18]
	}, options); 
	

	var locatePosition = function() {
		addToHistory();
		map.locate({
			setView : true,
			maxZoom : 14
		});
	};

	var addBackControl = function(pos) {
		controls.back = L.control({
			position : pos || 'topleft'
		});

		controls.back.onAdd = function(map) {

			var div = L.DomUtil.create('div', 'button-control back');
			L.DomEvent.addListener(div, 'click', function(event) {
				console.log('Click Back');
				restoreFromHistory();
				L.DomEvent.stopPropagation(event);
			});

			return div;
		};

		controls.back.addTo(map);
		
	};

	var addLocateControl = function(pos) {
		controls.locate = L.control({
			position : pos || 'bottomleft'
		});

		controls.locate.onAdd = function(map) {
			var div = L.DomUtil.create('div', 'button-control locate');
			L.DomEvent.addListener(div, 'click', function(event) {
				console.log('Click Locate');
				locatePosition();
				L.DomEvent.stopPropagation(event);
			});
			return div;
		};

		controls.locate.addTo(map);
	};
	
	var addDoneControl = function(pos) {
		controls.done = L.control({
			position : pos || 'topright'
		});
		var closeMap=function() {
			var container=$(map.getContainer());
			map.remove();
			container.remove();
		};
		controls.done.onAdd = function(map) {
			var cnt =L.DomUtil.create('div', 'button-container'),
			done = L.DomUtil.create('div', 'button-control done'),
			close = L.DomUtil.create('div', 'button-control close');
			cnt.appendChild(done);
			cnt.appendChild(close);
			L.DomEvent.addListener(close, 'click', function(event) {
				
				L.DomEvent.stopPropagation(event);
				closeMap();
			});
			L.DomEvent.addListener(done, 'click', function(event) {
				if (controls.done.onDone) {
					controls.done.onDone();
				}
				L.DomEvent.stopPropagation(event);
				closeMap();
			});
			return cnt;
		};

		controls.done.addTo(map);
	};
	
	var addCloseAsBackControl = function(pos) {
		controls.closeAsBack = L.control({
			position : pos || 'topright'
		});
		
		controls.closeAsBack.onAdd = function(map) {
			close = L.DomUtil.create('div', 'button-control close');
			L.DomEvent.addListener(close, 'click', function(event) {
				L.DomEvent.stopPropagation(event);
				history.back();
			});
			return close;
		};

		controls.closeAsBack.addTo(map);
	};

	
	var addLayersControl = function(pos) {
		controls.layers = L.control.layers(basicLayers, overlayLayers).addTo(map);
	};

	var updateLayersControl = function(base, overlay) {
		if (!controls.layers)
			return;

		var addLayers = function(from, to, cb) {
			for ( var name in from) {
				if (from.hasOwnProperty(name)) {
					to[name] = from[name];
					cb.call(controls.layers, from[name], name);
				}
			}
		};

		if (base) {
			addLayers(base, basicLayers, controls.layers.addBaseLayer);
		}
		if (overlay) {
			addLayers(overlay, overlayLayers, controls.layers.addOverlay);
		}
	};

	var addToHistory = function() {
		var pos = map.getBounds();
		if (mapHistory.length > 999) {
			mapHistory.shift();
		}
		mapHistory.push(pos);
	};

	var restoreFromHistory = function() {
		if (mapHistory.length > 0) {
			var h = mapHistory.pop();
			map.fitBounds(h);

		}
	};
	
	var centerOnPos=function(pos, delta) {
		delta = delta || 0;
		map.fitBounds([
				[ pos.lat - delta,
						pos.lng - delta ],
				[ pos.lat + delta,
						pos.lng + delta ] ]);
	};
	
	
	var GeoJson=L.GeoJSON.extend({
		getLayerId: function (layer) {
			var id=layer.feature.id;
			if (!id) throw "Place is missing id!";
			return id;
			}
	});

	function displayGroup(groupId, placeId) {
		var geojsonUrl = baseURL.replace('/99999', '/' + groupId),
		features, clusteredFeatures;
		
		var focusToPlace=function(placeId) {
			var place=features.getLayer(placeId);
			centerOnPos(place.getLatLng());
			addToHistory();
			place.openPopup();
		};

		var format_popup = function(props, place_id) {
			var html = '';
			var head = '<h3>' + props.name + '</h3>';
			if (props.url) {
				head = '<a href="' + props.url + '" target="_blank">' + 
				head + '</a>';
			}

			html += head;
			if (props.group) {
				html+='<a class="edit_btn_map button-control" href="#place/edit/'+props.group+
				'/'+place_id+'"></a>'
			}
			if (props.address) {
				html += '<p class="address">' + props.address + '</p>';
			}
			if (props.description) {
				html += '<p class="description">' + props.description + '</p>';
			}

			return html;
		};

		$.ajax({
			url : geojsonUrl,
			dataType : "json",
			success : function(geojson) {
				if (geojson.features.length<1) return;
				features = new GeoJson(geojson, {
					pointToLayer : function(feature, latlng) {
						return L.marker(latlng, {
							title : feature.properties.name
						});
					},
					onEachFeature : function(feature, layer) {

						if (feature.properties && feature.properties.name) {
							layer.bindPopup(format_popup(feature.properties, feature.id),{maxWidth:260});
							layer.on('click',
									function(event) {
										addToHistory();
										centerOnPos(event.latlng);
									});

						}
					}
				});
				clusteredFeatures = L.markerClusterGroup();
				clusteredFeatures.addLayer(features);
				clusteredFeatures.on('clusterclick', function(event) {
					addToHistory();
				});
				updateLayersControl(null, {
					'Places Clustered' : clusteredFeatures,
					'Places' : features
				});
				map.addLayer(clusteredFeatures);
				if (placeId) {
					focusToPlace(placeId);
				} else {
				map.fitBounds(clusteredFeatures.getBounds());
				}

			},
			error : function(req, status) {
				alert(gettext('Server Error: ') + status);
			}
		});

		var voronoiUrl = baseURL.replace('/99999', '/voronoi/' + groupId),
		voronoi = L.geoJson(null,{
			style : {
				"color" : "red",
				"weight" : 2,
				"opacity" : 0.5,
				'fillOpacity':0.01,
				'fill':false
			}});
		updateLayersControl(null, {
			'Voronoi' : voronoi
		});
		map.on('overlayadd',function (layer){
		
		if (layer.layer!==voronoi || layer.layer.voronoiLoaded) return;	
		
		$.ajax({
			url : voronoiUrl,
			dataType : 'json',
			error : function(req, status) {
				alert('Error ' + status);
			},
			success : function(geojson) {
				if (geojson.features.length<1) return;
				voronoi.addData(geojson);
				voronoi.voronoiLoaded=true;
				

			}

		});
		});
	}

	map = basicMap(elementId, mapOptions);

	map.on('locationfound', function(e) {
		if (currentPosition) {
			map.removeLayer(currentPosition);
		}

		currentPosition = L.circle(e.latlng, e.accuracy).addTo(map);

	});

	map.on('locationerror', function(e) {
		console.log('Location failed: ' + e.message);
	});
	
	var displayLocation=function(location, onLocationChange, pointInfo) {
		$(map.getContainer()).css('cursor', 'crosshair');
		var loc;
		try {
			loc=L.latLng(location);
			}	catch (exc) {
				console.log('Invalid location provided: '+exc);
			}
		if (loc) {
			displayKnownLocation(loc, onLocationChange, pointInfo);
		} else {
			displayKnownLocation([50.0874401, 14.4212556], onLocationChange, pointInfo, true);
			locatePosition();
		}
	};
	
	var displayKnownLocation=function(location, onLocationChange, pointInfo, skipMarker) {
	
		var canMove=true,
		marker;
		map.setView(location,18);
		var createMarker=function(pos) {
			marker=L.marker(pos, {draggable:true}).addTo(map);
			L.DomEvent.addListener(marker, 'click', function(event){
				var pos=marker.getLatLng();
				map.openPopup('<div class="position"><span class="lat">'+pos.lat+
					'</span>,<span class="lng">'+pos.lng +'</span></div>'+
					'<div class="address">'+pointInfo+'</div>', pos);
				L.DomEvent.stopPropagation(event);
			});
		};
		if (! skipMarker) { 
			createMarker(location);
		}
		controls.done.onDone=function(){
			if (onLocationChange && marker) {
				onLocationChange(marker.getLatLng());
			}
		};
		map.on('click', function(event) {
			if (canMove) {
			if (!marker) {
				createMarker(event.latlng);
			} else {
			marker.setLatLng(event.latlng);
			}
			}
		});
	};

	return {
		map : map,
		displayGroup : displayGroup,
		locatePosition : locatePosition,
		displayLocation: displayLocation
	};

};
