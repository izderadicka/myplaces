
var myPlacesApp=(function() {
	
	var router = null,
	lastSearch={},
	GroupModel = restAPI.Group,
	GroupsList = restAPI.GroupList,
	pgSize=5,
	leftPanel='#left_panel',
	rightPanel='#right_panel',
	fullSite=true;

/////////////////////////////////////////////////////////////////////////////////////////////////////////	
//utility functions
	
	var ListCache=function(modelClass) {
		var cache=this,
		list,
		options,
		callback=null,
		loadList=function(opt) {
			options=opt;
			list=new modelClass(options);
			list.fetch()
			.done(function(){
				if (callback) {
					callback(list);
				}
			})
			.fail(function(){
				cache.reset();
			});
			
		};
		
		
		$(document).on('data-update', function(event, model, action){
			var cacheType=modelClass.prototype.model.prototype.modelName,
			modelType=model.modelName;
			if (cacheType===modelType) {
				if (action==='add' ||action =='delete') {
					cache.reset();
				} 
				if (action=="change") {
					if (list && list.get(model)) {
						var oldModel=list.get(model);
						if (model !== oldModel) {
							var index=list.indexOf(oldModel);
							list.remove(oldModel);
							list.add(model, {at:index});
						}
					}
				}
				
					cache.handleMine(model, action);

			} else {
				
					cache.handleOther(model, action);
			}
			
		});
		
		var pendingUpdate=null;
		cache.updateIfCached= function(model) {
			if (list && list.get(model)) {
				pendingUpdate=list.get(model).fetch();
			}
			
		};
		cache.get=function(opt,fn) {
			if (list && _.isEqual(opt,options)) {
				$.when(pendingUpdate).always(function() {fn(list);});
			} else {
				callback=fn;
				loadList(opt);
			}
		};
		
		cache.peak=function() {
			return list;
		};
		
		cache.reset=function() {
			list=null;
			options=null;
		};
		
		return cache;
	};
	
	ListCache.extend=formsAPI.Widget.extend;
	_.extend(ListCache.prototype, {
		handleMine:function(model,action) {},
		handleOther:function(model,action) {}
	});
	
	PlaceListCache=ListCache.extend({
		handleMine: function(model,action) {
			if (action==='change' && model.onlyRelatedChanged) {
				this.updateIfCached(model);
			}
		}
		
	});
	
	GroupListCache=ListCache.extend({
		handleOther:function(model,action) {
			if (model.modelName==="Place" && (action==="add" || action==="delete")) {
				this.updateIfCached(model.get('group'));
			}
		}
	});
	
	
	var listCache={group: new GroupListCache(restAPI.PlacesGroupList),
			place: new PlaceListCache(restAPI.PlaceList)};
	
	var getOrLoad = function(name, model, id) {
		var g,
		list=listCache[name].peak(),
		d=$.Deferred();
		
		if (list && list.get(id)) {
			g = list.get(id);
			d.resolve(g);
		} else {
			g = new restAPI[model]({
				id : id
			});
			g.once('sync', function(){
				d.resolve(g);
			});
			g.fetch();
		}
		return d;
	};
	var getOrLoadGroup=_.partial(getOrLoad, 'group', 'PlacesGroup');
	var getOrLoadPlace=_.partial(getOrLoad, 'place', 'Place');
	
	
////////////////////////////////////////////////////////////////////////////////////////////////////
//views
	var EditView = formsAPI.FormView.extend({
		template : '#tbd',
		tagName : 'div',
		
		render: function() {
			this.$el.html(formsAPI.compileTemplate('#form_template')
					({fields:this.template(this.model.attributes),
						isNew:this.model.isNew()}));
			this.initForm();
		},

		events : {
			'click .save_btn' : 'saveModel',
			'click .cancel_btn' : 'cancelEdit',
			'click .confirm_delete_btn' : 'confirmDeleteModel',
			'click .close_dialog_btn': 'closeDialog',
			'click .delete_btn': 'deleteModel'
		},
		
		deleteModel: function() {
			var view=this;
			this.model.destroy();
			this.closeDialog();
			this.model.once('sync', function(){
				$(document).trigger('data-update', [view.model, 'delete']);
				router.nav(view.routeAfter(), {trigger:true});
			});
			
		},
		
		closeDialog:function() {
			$('.dialog, .cover', this.$el).remove();
		},
		
		confirmDeleteModel:function() {
			this.$el.append($('#confirm_delete').html());
			this.$el.append($('<div>').addClass('cover'));
		},
		
		cancelEdit:function() {
			router.nav(this.routeAfter(), {trigger:true});
		},
		afterSave: function() {
			if (this.wasNew) {
				$(document).trigger('data-update', [this.model, 'add']);
			} else {
				$(document).trigger('data-update', [this.model, 'change']);
			}
			router.nav(this.routeAfter(), {trigger:true});
		},
		
		routeAfter: function() { 
			return '/';
			},

		});
	
	var GroupEditView = EditView.extend({
		template : '#r2b_template_placesgroup',
		tagName : 'div',
		id : 'group_editor',
		
		
		});
	
	var PlaceEditView = EditView.extend({
		template : '#r2b_template_place',
		tagName : 'div',
		id : 'place_editor',
		
		
		events: _.extend(
			{'click .get_location_btn': 'getLocation',
			'click .get_address_btn': 'getAddress'
			}, EditView.prototype.events),
		
		render: function() {
			EditView.prototype.render.apply(this,arguments);
			var bar=formsAPI.compileTemplate('#geocode_bar');
			$('label[for="id_address"]', this.$el).parent().before($(bar()));
		},
		
		saveModel: function() {
			var deferredSaves=[],
			addressWidget=formsAPI.getWidget('address', this.$el);
			if (addressWidget.deferredSave) {
				deferredSaves.push(addressWidget.deferredSave);
			}
			
			EditView.prototype.saveModel.call(this, null, {deferredSaves:deferredSaves});
		},
		
		routeAfter: function() { 
			var group=this.model.get('group');
			if (group) return '/group/'+group;
			return '/';
			},
		
		
		getLocation: function() {
			var addressWidget=formsAPI.getWidget('address', this.$el),
			address=addressWidget.data,
			root=this.$el;
			if (!address || !address.toString() ) {
				alert(gettext('Address is empty, first define address to use geocoding'));
			} else {
				postJson('/mp/api/geocode', {address:address.attributes}, this)
				.done(function(data){
					if (! data.position) {
					alert(gettext('No location found for given address'));
					} else {
						var locationWidget=formsAPI.getWidget('position', root);
						locationWidget.set(data.position);
						
					}
				});
				
			}
		},
		
		getAddress: function() {
			var loc= formsAPI.getWidget('position', this.$el).get(),
			root=this.$el;
			if (!loc) alert(gettext('Location is empty, first define location to use geocoding'));
			postJson('/mp/api/geocode/reverse', {position:loc}, this)
			.done(function(data){
				if (! data.address) {
				alert(gettext('No address found for given location'));
				} else {
					var addressWidget=formsAPI.getWidget('address', root);
					addressWidget.openEditor(null, data.address);
				}
			});
			
		},
		
	});
	
	var postJson=function(url, data, syncOn) {
		if (syncOn) {
		if (syncOn._running) {
			alert(gettext('Another request is in progress, wait until it finishes'));
			return {done:function(){}};
		}
		syncOn._running=true;
		}
		var res= $.ajax({url:url,
			type:'POST',
			contentType: "application/json; charset=utf-8",
			dataType: "json",
			data: JSON.stringify(data),
		});
		res.always(function() {
			if (syncOn && syncOn._running) {
				syncOn._running=false;
			}
		})
		.fail(function(xhr, status, error){
				alert(gettext('Server Error: ')+status+' - '+error); 
			});
		return res;
	};
	
	var ListView=formsAPI.BaseListView.extend({
		templateItem : '#tbd',
		template : '#tbd',
		templateItemTitle : '#tbd',
		detailTemplate:"#tbd",
		tagName : 'div',
		
		events : {
			'click a.previous' : 'previousPage',
			'click a.next' : 'nextPage',
			'click li .title': 'expandItem'
		},
		
		getPK: function(event) {
			return $(event.currentTarget).parents('li[data-pk]').attr('data-pk');
		},
		
		expandItem: function(event) {
			var title=$(event.currentTarget),
			item=$(event.currentTarget).parents('li[data-pk]');
			if (title.hasClass('expanded')) {
				title.removeClass('expanded');
				$('.item-detail', item).empty();
			} else {
				var pk=item.attr('data-pk');
				title.addClass('expanded');
				$('.item-detail', item).html(
						formsAPI.compileTemplate(this.detailTemplate)(this.model.get(pk).attributes));
			}
		}
		
		
	});

	var GroupListView = ListView.extend({
		templateItem : '#group_item_template',
		template : '#groups_list_template',
		templateItemTitle : '#group_title_template',
		detailTemplate: '#group_detail',
		id : 'grs_list_wrapper',


		events : _.extend({
			'click .map_btn': 'openMap',
			'click .edit_btn': 'editGroup',
			'click .counter': 'showPlaces',
			}, ListView.prototype.events),
		
		
		showPlaces: function(event) {
			var pk=this.getPK(event);
			router.nav('/group/'+pk, {trigger:true});
		},
		
		editGroup: function(event) {
			var pk=this.getPK(event);
			router.nav('/group/edit/'+pk, {trigger:true});
		},
		
		openMap: function(event) {
			var pk=this.getPK(event);
			router.nav('/map/'+pk,{trigger:true} );
		}, 
		
	});
	
	var ViewWithList=formsAPI.BaseView.extend({
		template:'#tbd',
		listCache:null,
		listView:null,
		
		render: function() {
			var view=this;
			this.$el.html(this.template(this.model?this.model.attributes:{}));
			view.renderList();
		},
		
		events: {'click .search_btn': 'renderList',
			'keypress .search': 'searchOnEnter',
			'click .new_btn':  'routeToNew'
			},
		
		search: function() {
			var s=$('.search', this.$el);
			lastSearch[s.attr('id')]=s.val();
			this.renderList();
			
		},
		searchOnEnter: function(event) {
			if (event.which===13){
				this.search();
			}
		},
		routeToNew: function() {
			router.nav(this.getNewPath(), {trigger:true});
		},
		
		renderList: function() {
			var options={query:{ordering:'name'},
					pageSize : pgSize,
					pageSizeParam : 'page_size'
					},
			s=$('.search', this.$el),
			lookup=s.val(lastSearch[s.attr('id')]).val(),
			root=this.$el;
			if (lookup) {
				options.query.q=lookup;
			}
			
			if (this.extraQuery) {
				$.extend(options.query, this.extraQuery());
			}
			
			var listView=this.listView;
			this.listCache.get(options, function(list) {
				var view=new listView({model:list});
				view.render();
				$('.list_container',root).html(view.$el);
			});
		},
		
	});
	
	var GroupsView=ViewWithList.extend({
		template:'#groups_template',
		listCache:listCache.group,
		listView: GroupListView,
		
		getNewPath:function() {
			return '/group/new';
		}
	});
	
	var PlaceListView= ListView.extend({
		templateItem : '#place_item_template',
		template : '#groups_list_template',
		templateItemTitle : '#group_title_template',
		detailTemplate: '#place_template',
		id : 'places_list_wrapper',
		
		events : _.extend({
			'click .map_btn': 'openMap',
			'click .edit_btn': 'editPlace'
		}, ListView.prototype.events),
		
		openMap: function(event) {
			var pk=this.getPK(event);
			group=this.model.query.group;
			router.nav('/map/'+group+'/'+pk, {trigger:true});
		},
	
		editPlace: function(event) {
			var pk=this.getPK(event);
			router.nav('/place/edit/'+this.model.query.group+'/'+pk, {trigger:true} );
			
		}
		
	});
	
	var GroupDetailView=ViewWithList.extend({
		template:'#group_places_detail',
		listCache:listCache.place,
		listView:PlaceListView,

		getNewPath:function() {
			return '/place/new/'+this.model.id;
		},
		extraQuery:function() {
			return {group:this.model.id};
		}
	});
	
//////////////////////////////////////////////////////////////////////////////////////////////////////////////	
// router/controller
	
	var App = Backbone.Router.extend({
		routes : {
			"group/new" : "addGroup",
			"group/edit/:id" : "editGroup",
			"place/edit/:group/:id" : "editPlace",
			"place/new/:group": 'addPlace',
			"group/:id": "groupDetail",
			"map/:gid": "showMap",
			"map/:gid/:id": "showMap",
			"" : "defaultRoute"

		},

		showMap: function(gid,id){
			
			var map=$('<div>').attr('id', 'map').appendTo('body');
			window.scrollTo(0,0);
			$('#map').show();
			showMap(gid,id);
			
		},
		
		editGroup : function(id) {
			if (fullSite) {
				this.listGroups();
			}		
			getOrLoadGroup(id).done(function(g) {
			var v = new GroupEditView({
				model : g
			});
			v.render();
			$(rightPanel).html(v.$el);
			});
		},
		
		editPlace : function(gid,id) {
			if (fullSite) {
				this.groupDetailAlone(gid);
			}
			getOrLoadPlace(id).done(function(g) {
			var v = new PlaceEditView({
				model : g
			});
			v.render();
			$(leftPanel).html(v.$el);
			});
		},
		
		addPlace : function(gid) {
			
			if (fullSite) {
				this.groupDetailAlone(gid);
			}
			
			var place=new restAPI.Place();
			place.set('group', gid);
			var v = new PlaceEditView({
				model : place
			});
			v.wasNew=true;
			v.render();
			$(leftPanel).html(v.$el);
		},

		addGroup : function(id) {
			if (fullSite) {
				this.listGroups();
			}
			var g = new restAPI.PlacesGroup();
			var v = new GroupEditView({
				model : g
			});
			v.wasNew=true;
			v.render();
			$(rightPanel).html(v.$el);
		},

		listGroups : function() {
			var v=new GroupsView();
			v.render();
			$(leftPanel).html(v.$el);
			
		},
		
		groupDetail: function(id) {
			if (fullSite) {
				this.listGroups();
			}
			this.groupDetailAlone(id);
		},
		
		groupDetailAlone:function(id) {
			getOrLoadGroup(id).done(function(g) {
				var v = new GroupDetailView({
					model : g
				});
				v.render();
				$(rightPanel).html(v.$el);
				});
		},

		defaultRoute : function() {
			if (fullSite) {
			$(rightPanel).html($('#initial_banner').html());
			}
			this.listGroups();
		},
		
		// overide  to get event before   route is executed	
		route : function(route, name, callback) {
			if (!_.isRegExp(route))
				route = this._routeToRegExp(route);
			if (_.isFunction(name)) {
				callback = name;
				name = '';
			}
			if (!callback)
				callback = this[name];
			var router = this;
			Backbone.history.route(route, function(fragment) {
				var args = router._extractParameters(route, fragment);
				router.trigger('before-route', name, args);
				if (callback)  callback.apply(router, args);
				router.trigger.apply(router, [ 'route:' + name ].concat(args));
				router.trigger('route', name, args);
				Backbone.history.trigger('route', router, name, args);
			});
			return this;
		},

	});
	
	
	router = new App();
	router.nav=function(fragment,options) {
		this.navigate(fragment,options);
	};
	
	router.on('before-route', function() {
		$('#map').remove();
	});
	
/////////////////////////////////////////////////////////////////////////////////////////////////////////	
// main UI utilities
	
	var toggleMenu=function(event) {
		if ($('#main_menu_displayed').length>0) {
			$('#main_menu_displayed').remove();
		} else {
			var m=$('<div>').attr('id', 'main_menu_displayed').mouseleave(function() {
				m.remove();
			})
			.html($('#main_menu').html()).on('click', 'a', function() {
				m.remove();
			});
			$('body').append(m);
		}
	};
	
	
	var init=function(flavour) {
	if (flavour=="full") {
		pgSize=10;
		leftPanel='#left_panel';
		rightPanel='#right_panel';
		fullSite=true;
	} else {
		pgSize=8;
		leftPanel='#one_panel';
		rightPanel='#one_panel';
		fullSite=false;
	}
	$('#menu_btn').click(toggleMenu);
	$( document ).ajaxStart(function() {
		$('#ajax_indicator').show();
	});
	
	$( document ).ajaxStop(function() {
		$('#ajax_indicator').hide();
	});
	Backbone.history.start();
	};
	
	return {init:init, 
		router:router};

})();

//////////////////////////////////////////////////////////////////////////////////////////////////
// Custom widgets

var customWidgets= (function () {
	var w={};
	w.Location=formsAPI.Widget.extend({
		getValue:function() {
			var raw=_.map($('input', this.elem).val().split(','),
					function(x) {return x.trim();}),
			numRe=/^\d+\.?\d*$/;
			if (raw.length!=2) return this.error(gettext('Location format must be lat,lng'));
			for (var i=0; i<raw.length; i+=1 ) {
				if (!numRe.test(raw[i])) return this.error(gettext('Not a number: '+raw[i]));
			}
			var lat=parseFloat(raw[0]), 
			lng=parseFloat(raw[1]);
			
			if (lat>90 || lat<-90) return this.error(gettext('Latitude is outside of range'));
			if (lng>180 || lng<-180) return this.error(gettext('Longitude is outside of range'));
			return [lat,lng];
		},
		setValue:function(value) {
			$('input', this.elem).val(value.toString());
		},
		events: {'click .map_btn': 'showMap'},
		showMap: function() {
			
			var map=$('<div>').attr('id', 'map').appendTo($('body'));
			window.scrollTo(0,0);
			map.show();
			var widget=this;
			var round=function(x) {return Math.round(x*10000000)/10000000;};
			var updateLocation=function(loc) {
				widget.set([round(loc.lat), round(loc.lng)]);
			};
			var addressWidget=formsAPI.getWidget('address', this.options.view.$el),
			pointInfo= addressWidget.data?addressWidget.data.toString():'';
			
			showMapAsSelector(this.getValue(), updateLocation, pointInfo);
			
			
		}
	});
	
	//TODO: path toString of Address
	restAPI.Address.prototype.toString=function () {
		var self=this.attributes;
        var addr=[],
        append_if_exists = function(item){
                if (item) addr.push(item);
        };
        append_if_exists(self.street);
        append_if_exists( self.postal_code?self.postal_code+' '+self.city: self.city);
        append_if_exists(self.county);
        append_if_exists(self.state);
        append_if_exists(self.country);
        if (addr.length>0) {
            return addr.join(', ');
		}
        else {
            return self.unformatted || '';
        }
	};
	
	
	return w;
})();

///////////////////////////////////////////////////////////////////////////////////////////////////
// Start Application

$(function() {
	myPlacesApp.init(siteFlavour);
	
});
